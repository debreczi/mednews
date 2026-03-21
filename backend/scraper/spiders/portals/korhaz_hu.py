from ..rss_spider import RssSpider


class KorhazHuSpider(RssSpider):
    name = "korhaz_hu"
    start_urls = ["https://korhaz.hu/feed"]
    feed_name = "Kórház.hu"
