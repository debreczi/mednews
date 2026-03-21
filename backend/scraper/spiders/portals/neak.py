from ..rss_spider import RssSpider


class NeakSpider(RssSpider):
    name = "neak"
    start_urls = ["https://neak.gov.hu/feed"]
    feed_name = "NEAK"
