from ..rss_spider import RssSpider


class PatikamagazinSpider(RssSpider):
    name = "patikamagazin"
    start_urls = ["https://patikamagazin.hu/feed"]
    feed_name = "Patika Magazin"
