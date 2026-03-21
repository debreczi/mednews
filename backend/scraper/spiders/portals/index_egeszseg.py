from ..rss_spider import RssSpider


class IndexEgeszsegSpider(RssSpider):
    name = "index_egeszseg"
    start_urls = ["https://index.hu/24ora/rss/?rovat=egeszseg"]
    feed_name = "Index Egészség"
