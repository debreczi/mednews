from ..rss_spider import RssSpider


class MedicusanonymusSpider(RssSpider):
    name = "medicusanonymus"
    start_urls = ["https://medicusanonymus.hu/feed"]
    feed_name = "Medicus Anonymus"
