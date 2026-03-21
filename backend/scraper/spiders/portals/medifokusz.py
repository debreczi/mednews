from ..rss_spider import RssSpider


class MedifokuszSpider(RssSpider):
    name = "medifokusz"
    start_urls = ["https://medifokusz.hu/feed"]
    feed_name = "MediFókusz"
