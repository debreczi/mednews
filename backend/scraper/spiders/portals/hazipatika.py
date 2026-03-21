from ..rss_spider import RssSpider


class HazipatikaSider(RssSpider):
    name = "hazipatika"
    start_urls = ["https://www.hazipatika.com/rss.xml"]
    feed_name = "Házipatika"
