"""Base spider — all MedNews spiders inherit from this."""
import hashlib
import logging
from datetime import datetime
from typing import Any, Generator

import scrapy
from itemadapter import ItemAdapter


class MedNewsItem(scrapy.Item):
    url = scrapy.Field()
    original_title = scrapy.Field()
    mednews_title = scrapy.Field()
    summary = scrapy.Field()
    link_text = scrapy.Field()
    source_text = scrapy.Field()
    image_url = scrapy.Field()
    date_collected = scrapy.Field()
    date_published = scrapy.Field()
    relevance_score = scrapy.Field()
    is_tragic = scrapy.Field()
    enrichment_status = scrapy.Field()
    source_id = scrapy.Field()


class BaseSpider(scrapy.Spider):
    """Base class for all MedNews spiders.

    Subclasses must define:
        name: str
        start_urls: list[str]
        source_type: str  — 'portal' | 'rss' | 'social' | 'international'

    Subclasses should implement:
        parse_article(response) → MedNewsItem
    """

    source_type: str = "portal"
    custom_settings: dict[str, Any] = {}

    def parse(self, response) -> Generator:
        raise NotImplementedError("Subclass must implement parse()")

    def make_item(
        self,
        url: str,
        original_title: str,
        image_url: str | None = None,
        date_published: datetime | None = None,
        source_id: int | None = None,
    ) -> MedNewsItem:
        """Create a pre-populated MedNewsItem with defaults."""
        item = MedNewsItem()
        item["url"] = url
        item["original_title"] = original_title.strip()
        item["mednews_title"] = None
        item["summary"] = None
        item["link_text"] = None
        item["source_text"] = None
        item["image_url"] = image_url
        item["date_collected"] = datetime.utcnow()
        item["date_published"] = date_published
        item["relevance_score"] = 0.0  # set by scorer pipeline
        item["is_tragic"] = False      # set by enrichment service
        item["enrichment_status"] = "pending"
        item["source_id"] = source_id
        return item

    def handle_error(self, failure):
        self.logger.error(f"[{self.name}] Request failed: {failure.request.url} — {failure.value}")
