"""Async runner — fetches RSS feeds and Twitter/X timelines.

Fetches each feed with feedparser (via thread executor), scores and
enriches with the existing service layer, then persists to SQLite.
Twitter sources use the v2 API with Bearer token auth.
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

    # Split sources by type
    rss_sources = [s for s in sources if s.type != "twitter"]
    twitter_sources = [s for s in sources if s.type == "twitter"]

    logger.info(f"[Runner] Fetching {len(rss_sources)} RSS + {len(twitter_sources)} Twitter sources...")

    tasks = [_fetch_source(src, existing_urls) for src in rss_sources]
    if twitter_sources:
        tasks.extend([_fetch_twitter_source(src, existing_urls) for src in twitter_sources])

    all_sources = rss_sources + twitter_sources
    results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_articles = []
    stats = {"found": 0, "saved": 0, "errors": 0}

    for src, result in zip(all_sources, results):
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


async def _fetch_twitter_source(source, existing_urls: set) -> list:
    """Fetch recent tweets from a Twitter/X account via v2 API.

    The source.url should be like https://x.com/username — we extract the
    username and call the v2 user tweets endpoint.
    """
    from ..config import settings

    token = settings.twitter_bearer_token
    if not token:
        raise RuntimeError("TWITTER_BEARER_TOKEN not configured")

    # Extract username from URL (https://x.com/username or https://twitter.com/username)
    username = source.url.rstrip("/").split("/")[-1].lstrip("@")

    # Use a separate client for Twitter API (longer timeout, custom transport)
    twitter_client = httpx.AsyncClient(
        timeout=20, follow_redirects=True,
        headers={
            "User-Agent": "MedNews/1.0",
            "Authorization": f"Bearer {token}",
        },
    )
    _TWITTER_API = "https://api.x.com"

    try:
        # Step 1: resolve username → user ID
        async with _SEMAPHORE:
            user_resp = await twitter_client.get(
                f"{_TWITTER_API}/2/users/by/username/{username}",
            )
        if user_resp.status_code != 200:
            raise RuntimeError(f"Twitter user lookup failed ({user_resp.status_code}): {user_resp.text[:200]}")

        user_data = user_resp.json().get("data")
        if not user_data:
            raise RuntimeError(f"Twitter user @{username} not found")
        user_id = user_data["id"]

        # Step 2: fetch recent tweets (last 7 days max, up to 10 per account)
        async with _SEMAPHORE:
            tweets_resp = await twitter_client.get(
                f"{_TWITTER_API}/2/users/{user_id}/tweets",
                params={
                    "max_results": 10,
                    "tweet.fields": "created_at,text,entities",
                    "exclude": "retweets,replies",
                },
            )
        if tweets_resp.status_code != 200:
            raise RuntimeError(f"Twitter tweets fetch failed ({tweets_resp.status_code}): {tweets_resp.text[:200]}")

        tweets = tweets_resp.json().get("data", [])
        articles = []

        for tweet in tweets:
            tweet_url = f"https://x.com/{username}/status/{tweet['id']}"
            if tweet_url in existing_urls:
                continue
            existing_urls.add(tweet_url)

            # Extract first URL from tweet entities (the linked article)
            article_url = None
            entities = tweet.get("entities", {})
            for u in entities.get("urls", []):
                expanded = u.get("expanded_url", "")
                # Skip twitter/x.com self-links
                if "twitter.com" not in expanded and "x.com" not in expanded:
                    article_url = expanded
                    break

            # Parse date
            date_published = None
            if tweet.get("created_at"):
                try:
                    date_published = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
                except Exception:
                    pass

            # Use linked article URL if available, otherwise the tweet URL
            url = article_url or tweet_url
            if url in existing_urls and url != tweet_url:
                continue
            existing_urls.add(url)

            # Truncate tweet text to use as title
            text = tweet.get("text", "").strip()
            # Remove t.co links from display title
            title = re.sub(r"https?://t\.co/\S+", "", text).strip()
            if not title:
                continue

            articles.append({
                "url": url,
                "original_title": title[:300],
                "image_url": None,
                "date_published": date_published,
                "date_collected": datetime.now(timezone.utc),
                "source_id": source.id,
                "source_text": f"@{username}",
                "relevance_score": 0.0,
                "is_tragic": False,
                "enrichment_status": "pending",
            })

        return articles
    finally:
        await twitter_client.aclose()


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
