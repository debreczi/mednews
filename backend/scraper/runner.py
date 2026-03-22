"""Async RSS runner — replaces Scrapy for all RSS sources.

Fetches each feed with feedparser (via thread executor), scores and
enriches with the existing service layer, then persists to SQLite.
No Twisted, no reactor, no Playwright for RSS feeds.
"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

logger = logging.getLogger(__name__)

# Max concurrent feed fetches
_SEMAPHORE = asyncio.Semaphore(8)
_HTTP_CLIENT: httpx.AsyncClient | None = None

_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_RE2 = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    re.IGNORECASE,
)


async def run_all_spiders() -> dict:
    """Fetch all active RSS sources, score, enrich, and save articles.

    Returns aggregate stats: {"found": N, "saved": N, "errors": N}
    """
    from ..database import SessionLocal
    from ..models.source import Source
    from sqlalchemy import select

    with SessionLocal() as db:
        sources = list(db.scalars(select(Source).where(Source.active == True)).all())

    if not sources:
        logger.warning("[Runner] No active sources found")
        return {"found": 0, "saved": 0, "errors": 0}

    # Load existing URLs to skip duplicates across all sources
    existing_urls = _load_existing_urls()

    logger.info(f"[Runner] Fetching {len(sources)} RSS sources...")

    tasks = [_fetch_source(src, existing_urls) for src in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_articles = []
    stats = {"found": 0, "saved": 0, "errors": 0}

    for src, result in zip(sources, results):
        if isinstance(result, Exception):
            logger.error(f"[Runner] {src.name} fetch failed: {result}")
            stats["errors"] += 1
        else:
            stats["found"] += len(result)
            raw_articles.extend(result)

    if not raw_articles:
        logger.info("[Runner] No new articles found")
        return stats

    logger.info(f"[Runner] {len(raw_articles)} new articles — scoring...")
    saved = await _score_enrich_save(raw_articles)
    stats["saved"] = saved

    logger.info(f"[Runner] Run complete: {stats}")
    return stats


def _load_existing_urls() -> set:
    from ..database import SessionLocal
    from ..models.article import Article
    from sqlalchemy import select
    try:
        with SessionLocal() as db:
            return set(db.scalars(select(Article.url)).all())
    except Exception as e:
        logger.warning(f"[Runner] Could not load existing URLs: {e}")
        return set()


async def _get_http_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None or _HTTP_CLIENT.is_closed:
        _HTTP_CLIENT = httpx.AsyncClient(
            timeout=10, follow_redirects=True,
            headers={"User-Agent": "MedNews/1.0 (RSS aggregator)"},
        )
    return _HTTP_CLIENT


async def _fetch_og_image(url: str) -> str | None:
    """Fetch an article page and extract og:image meta tag."""
    try:
        client = await _get_http_client()
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        # Only scan the first 50KB for performance
        head = resp.text[:50_000]
        match = _OG_IMAGE_RE.search(head) or _OG_IMAGE_RE2.search(head)
        return match.group(1) if match else None
    except Exception:
        return None


async def _fetch_source(source, existing_urls: set) -> list:
    """Fetch one RSS feed and return list of new article dicts."""
    async with _SEMAPHORE:
        loop = asyncio.get_event_loop()
        try:
            feed = await loop.run_in_executor(None, feedparser.parse, source.url)
        except Exception as e:
            raise RuntimeError(f"feedparser failed: {e}") from e

    articles = []
    for entry in feed.entries:
        link = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not link or not title or link in existing_urls:
            continue

        existing_urls.add(link)  # prevent duplicates within this run

        # Parse publish date
        date_published = None
        pub = entry.get("published") or entry.get("updated")
        if pub:
            try:
                date_published = parsedate_to_datetime(pub)
            except Exception:
                pass

        # Extract image
        image_url = None
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get("url")
        elif hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image/"):
                    image_url = enc.get("url")
                    break

        articles.append({
            "url": link,
            "original_title": title,
            "image_url": image_url,
            "date_published": date_published,
            "date_collected": datetime.now(timezone.utc),
            "source_id": source.id,
            "source_text": source.name,
            "relevance_score": 0.0,
            "is_tragic": False,
            "enrichment_status": "pending",
        })

    return articles


async def _score_enrich_save(articles: list) -> int:
    """Score, filter, enrich, and persist articles. Returns count saved."""
    from ..services.scorer import score_and_filter
    from ..services.enrichment import enrich_articles
    from ..config import settings
    from ..database import SessionLocal
    from ..models.article import Article
    from sqlalchemy.exc import IntegrityError

    # Score and filter
    scoreable = [{"original_title": a["original_title"], "_raw": a} for a in articles]
    scored = await score_and_filter(scoreable, settings.relevance_threshold)

    if not scored:
        logger.info("[Runner] No articles passed relevance threshold")
        return 0

    logger.info(f"[Runner] {len(scored)} articles passed scoring — enriching...")

    # Fetch og:image for articles missing images
    needs_image = [s for s in scored if not s["_raw"].get("image_url")]
    if needs_image:
        logger.info(f"[Runner] Fetching og:image for {len(needs_image)} articles...")
        og_tasks = [_fetch_og_image(s["_raw"]["url"]) for s in needs_image]
        og_results = await asyncio.gather(*og_tasks)
        for s, img in zip(needs_image, og_results):
            if img:
                s["_raw"]["image_url"] = img

    # Re-attach raw article data
    for s in scored:
        s["_raw"]["relevance_score"] = s["relevance_score"]

    to_enrich = [{"original_title": s["original_title"], "_raw": s["_raw"]} for s in scored]
    enriched = await enrich_articles(to_enrich)

    # Save to DB
    saved = 0
    with SessionLocal() as db:
        for item in enriched:
            raw = item.pop("_raw", {})
            raw.update({k: item.get(k) for k in
                        ("mednews_title", "summary", "link_text", "is_tragic", "enrichment_status")
                        if k in item})
            # Remove internal keys
            raw.pop("_item", None)

            article = Article(
                url=raw["url"],
                original_title=raw["original_title"],
                mednews_title=raw.get("mednews_title"),
                summary=raw.get("summary"),
                link_text=raw.get("link_text"),
                source_text=raw.get("source_text"),
                image_url=raw.get("image_url"),
                date_collected=raw.get("date_collected"),
                date_published=raw.get("date_published"),
                relevance_score=raw.get("relevance_score", 0.0),
                is_tragic=raw.get("is_tragic", False),
                enrichment_status=raw.get("enrichment_status", "complete"),
                source_id=raw.get("source_id"),
            )
            try:
                db.add(article)
                db.commit()
                saved += 1
            except IntegrityError:
                db.rollback()

    logger.info(f"[Runner] Saved {saved} articles")
    return saved
