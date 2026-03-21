from ..rss_spider import RssSpider


class EgeszsegkalauzSpider(RssSpider):
    name = "egeszsegkalauz"
    start_urls = ["https://www.egeszsegkalauz.hu/feed"]
    feed_name = "EgészségKalauz"
