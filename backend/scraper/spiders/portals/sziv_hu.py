from ..rss_spider import RssSpider


class SzivHuSpider(RssSpider):
    name = "sziv_hu"
    start_urls = ["https://sziv.hu/feed"]
    feed_name = "Szív.hu"
