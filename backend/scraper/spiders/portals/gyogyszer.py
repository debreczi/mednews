from ..rss_spider import RssSpider


class GyogyszerSpider(RssSpider):
    name = "gyogyszer"
    start_urls = ["https://www.gyogyszer.hu/feed"]
    feed_name = "Gyógyszer.hu"
