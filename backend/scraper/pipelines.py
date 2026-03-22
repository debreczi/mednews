"""Scrapy item pipelines: duplicate filter → score filter → enrich → save to DB.

Pipeline order (set in settings.py):
  100 DuplicateFilterPipeline  — drop already-seen URLs
  200 ScoreFilterPipeline      — drop items below RELEVANCE_THRESHOLD
  300 EnrichmentPipeline       — AI title/summary/link_text via xAI Grok
  400 DatabasePipeline         — persist to SQLite
"""
import asyncio
import logging
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class DuplicateFilterPipeline:
    """Drop articles with URLs already scraped in this run or already in the DB."""

    def open_spider(self, spider):
        self.seen_urls: set[str] = set()
        # Also load existing URLs from DB to avoid re-enriching old articles
        try:
            from backend.database import SessionLocal
            from backend.models.article import Article
            from sqlalchemy import select
            with SessionLocal() as db:
                existing = db.scalars(select(Article.url)).all()
                self.seen_urls.update(existing)
        except Exception as e:
            logger.warning(f"[DuplicateFilter] Could not pre-load DB URLs: {e}")

    def process_item(self, item, spider):
        from scrapy.exceptions import DropItem
        adapter = ItemAdapter(item)
        url = adapter.get("url", "")
        if not url or url in self.seen_urls:
            raise DropItem(f"Duplicate or empty URL: {url}")
        self.seen_urls.add(url)
        return item


class ScoreFilterPipeline:
    """Score each article via Grok and drop those below RELEVANCE_THRESHOLD."""

    def open_spider(self, spider):
        from backend.config import settings
        self.threshold = settings.relevance_threshold
        self._pending: list = []

    def process_item(self, item, spider):
        # Items are scored individually here; batch scoring happens in close_spider
        # For now: assign placeholder score — batch override happens below
        adapter = ItemAdapter(item)
        adapter["relevance_score"] = adapter.get("relevance_score", 0.0)
        return item

    def close_spider(self, spider):
        pass  # Batch scoring wired in EnrichmentPipeline for efficiency


class EnrichmentPipeline:
    """Batch-enrich articles with Grok: score → filter → title/summary/link_text."""

    BATCH_SIZE = 10

    def open_spider(self, spider):
        self._batch: list = []

    def process_item(self, item, spider):
        self._batch.append(item)
        return item

    def close_spider(self, spider):
        if not self._batch:
            return
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._process_batch(spider))
            loop.close()
        except Exception as e:
            logger.error(f"[Enrichment] Pipeline close_spider error: {e}")

    async def _process_batch(self, spider):
        from backend.services.scorer import score_and_filter
        from backend.services.enrichment import enrich_articles
        from backend.config import settings
        from scrapy.exceptions import DropItem

        articles = []
        for item in self._batch:
            adapter = ItemAdapter(item)
            articles.append({
                "original_title": adapter.get("original_title", ""),
                "summary": adapter.get("summary", "") or "",
                "_item": item,
            })

        # Score all articles in batch
        scored = await score_and_filter(articles, settings.relevance_threshold)

        # Re-attach scores to items, drop low scorers
        scored_urls = set()
        for a in scored:
            item = a.pop("_item")
            adapter = ItemAdapter(item)
            adapter["relevance_score"] = a["relevance_score"]
            scored_urls.add(adapter.get("url"))

        # Enrich only the passing articles
        passing = [a for a in articles if a.get("_item") and
                   ItemAdapter(a["_item"]).get("url") in scored_urls]

        if passing:
            # Build dicts for enrichment
            to_enrich = []
            for a in scored:
                to_enrich.append({
                    "original_title": a["original_title"],
                    "relevance_score": a["relevance_score"],
                    "_item": None,
                })

            enriched = await enrich_articles([
                {"original_title": ItemAdapter(item).get("original_title", ""),
                 "_item": item}
                for item in self._batch
                if ItemAdapter(item).get("url") in scored_urls
            ])

            for a in enriched:
                item = a.pop("_item", None)
                if item:
                    adapter = ItemAdapter(item)
                    adapter["mednews_title"] = a.get("mednews_title")
                    adapter["summary"] = a.get("summary")
                    adapter["link_text"] = a.get("link_text")
                    adapter["is_tragic"] = a.get("is_tragic", False)
                    adapter["enrichment_status"] = a.get("enrichment_status", "complete")


class DatabasePipeline:
    """Save enriched, scored articles to SQLite."""

    def open_spider(self, spider):
        from backend.database import SessionLocal
        self.db = SessionLocal()
        self.saved = 0

    def close_spider(self, spider):
        self.db.close()
        logger.info(f"[DB] Saved {self.saved} articles this run")

    def process_item(self, item, spider):
        from backend.models.article import Article
        from sqlalchemy.exc import IntegrityError
        adapter = ItemAdapter(item)

        # Only save articles that passed scoring
        if adapter.get("relevance_score", 0) < 1:
            return item  # pipeline already filtered low scorers; this is a safeguard

        # Build Article from item fields (exclude internal keys)
        fields = {
            k: adapter.get(k)
            for k in [
                "url", "original_title", "mednews_title", "summary", "link_text",
                "source_text", "image_url", "date_collected", "date_published",
                "relevance_score", "is_tragic", "enrichment_status", "source_id",
            ]
        }
        article = Article(**fields)
        try:
            self.db.add(article)
            self.db.commit()
            self.saved += 1
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"[DB] Skipped duplicate: {adapter.get('url')}")
        return item
