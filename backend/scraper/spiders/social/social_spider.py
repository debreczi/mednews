"""Social media spider stub.

LinkedIn, Facebook, and Instagram block automated scraping aggressively.
This stub documents the intended behavior and logs the limitation.
Real implementation requires official APIs or carefully rate-limited playwright sessions.
Registered in Spec Drift Log: social pages yield 0 items via scraping.
"""
import logging
from ..base_spider import BaseSpider

logger = logging.getLogger(__name__)


class SocialSpider(BaseSpider):
    """Stub spider for social media sources (LinkedIn, Facebook, Instagram).

    These platforms block scraping. This spider logs a warning and exits cleanly.
    Source auto-discovery (Phase 3) will surface social content via Grok web search.
    """
    name = "social_spider"
    source_type = "social"
    start_urls = []

    def parse(self, response):
        logger.warning(
            f"[SocialSpider] Social media scraping blocked on {response.url}. "
            "Use official APIs or source_discovery for social content."
        )
        return []
