from ..rss_spider import RssSpider


class MedicalonlineSpider(RssSpider):
    name = "medicalonline"
    start_urls = ["https://medicalonline.hu/feed"]
    feed_name = "Medical Online"
