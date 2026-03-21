from ..rss_spider import RssSpider


class PszichiaterSpider(RssSpider):
    name = "pszichiater"
    start_urls = ["https://www.pszichiater.hu/feed"]
    feed_name = "Pszichiáter.hu"
