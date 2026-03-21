"""Generic parametric RSS spider. One instance per RSS source."""
import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime

import scrapy
from .base_spider import BaseSpider, MedNewsItem


class RssSpider(BaseSpider):
    """Scrapes any RSS feed. Parametric: pass -a url=<feed_url> -a name=<name>."""

    name = "rss_spider"
    source_type = "rss"

    def __init__(self, url: str = "", feed_name: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feed_url = url
        self.feed_name = feed_name or url
        self.start_urls = [url] if url else []

    def parse(self, response):
        feed = feedparser.parse(response.text)
        for entry in feed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "").strip()
            if not link or not title:
                continue

            # Parse publish date
            date_published = None
            if hasattr(entry, "published"):
                try:
                    date_published = parsedate_to_datetime(entry.published)
                except Exception:
                    pass

            # Extract image if present
            image_url = None
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                for enc in entry.enclosures:
                    if enc.get("type", "").startswith("image/"):
                        image_url = enc.get("url")
                        break

            item = self.make_item(
                url=link,
                original_title=title,
                image_url=image_url,
                date_published=date_published,
            )
            yield item
