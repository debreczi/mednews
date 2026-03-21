from ..rss_spider import RssSpider


class HimssSpider(RssSpider):
    name = "himss"
    start_urls = ["https://www.himss.org/news/rss.xml"]
    feed_name = "HIMSS News"
