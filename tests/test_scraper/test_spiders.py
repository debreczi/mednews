"""Tests for spider infrastructure."""
import pytest
from scrapy.http import HtmlResponse, Request
from backend.scraper.spiders.base_spider import BaseSpider, MedNewsItem
from backend.scraper.spiders.rss_spider import RssSpider


class ConcreteSpider(BaseSpider):
    name = "test_spider"
    def parse(self, response):
        yield self.make_item(url="https://example.com", original_title="Test")


class TestBaseSpider:
    def setup_method(self):
        self.spider = ConcreteSpider()

    def test_make_item_defaults(self):
        item = self.spider.make_item(url="https://example.com/a", original_title="Title")
        assert item["url"] == "https://example.com/a"
        assert item["original_title"] == "Title"
        assert item["mednews_title"] is None
        assert item["enrichment_status"] == "pending"
        assert item["relevance_score"] == 0.0
        assert item["is_tragic"] is False

    def test_make_item_with_image(self):
        item = self.spider.make_item(
            url="https://example.com/b",
            original_title="Title",
            image_url="https://example.com/img.jpg"
        )
        assert item["image_url"] == "https://example.com/img.jpg"

    def test_make_item_strips_title(self):
        item = self.spider.make_item(url="https://x.com", original_title="  Padded Title  ")
        assert item["original_title"] == "Padded Title"


class TestRssSpider:
    RSS_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Test Feed</title>
        <item>
          <title>Article One</title>
          <link>https://example.com/article-1</link>
          <pubDate>Fri, 01 Mar 2024 10:00:00 +0000</pubDate>
        </item>
        <item>
          <title>Article Two</title>
          <link>https://example.com/article-2</link>
        </item>
      </channel>
    </rss>"""

    def _make_response(self, url="https://example.com/rss.xml"):
        return HtmlResponse(
            url=url,
            body=self.RSS_CONTENT.encode("utf-8"),
            encoding="utf-8",
        )

    def test_parses_items(self):
        spider = RssSpider(url="https://example.com/rss.xml")
        response = self._make_response()
        items = list(spider.parse(response))
        assert len(items) == 2

    def test_item_fields(self):
        spider = RssSpider(url="https://example.com/rss.xml")
        response = self._make_response()
        items = list(spider.parse(response))
        assert items[0]["original_title"] == "Article One"
        assert items[0]["url"] == "https://example.com/article-1"

    def test_skips_items_without_link(self):
        no_link_rss = self.RSS_CONTENT.replace(
            "<link>https://example.com/article-1</link>", ""
        )
        spider = RssSpider(url="https://example.com/rss.xml")
        response = HtmlResponse(
            url="https://example.com/rss.xml",
            body=no_link_rss.encode("utf-8"),
            encoding="utf-8",
        )
        items = list(spider.parse(response))
        # Article without link should be skipped
        urls = [i["url"] for i in items]
        assert "" not in urls

    def test_parses_pubdate(self):
        spider = RssSpider(url="https://example.com/rss.xml")
        response = self._make_response()
        items = list(spider.parse(response))
        assert items[0]["date_published"] is not None

    def test_no_pubdate_is_none(self):
        spider = RssSpider(url="https://example.com/rss.xml")
        response = self._make_response()
        items = list(spider.parse(response))
        assert items[1]["date_published"] is None


def test_spider_count():
    """AC-2: Verify at least 50 spider classes exist in the spiders package."""
    import importlib
    import pkgutil
    import inspect
    import backend.scraper.spiders as spiders_pkg

    count = 0
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=spiders_pkg.__path__,
        prefix=spiders_pkg.__name__ + ".",
        onerror=lambda x: None,
    ):
        try:
            module = importlib.import_module(modname)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BaseSpider)
                    and obj is not BaseSpider
                    and obj.__module__ == modname
                ):
                    count += 1
        except Exception:
            pass

    assert count >= 50, f"Only {count} spider classes found — need at least 50 (AC-2)"
