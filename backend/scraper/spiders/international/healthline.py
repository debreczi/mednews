from ..rss_spider import RssSpider


class HealthlineSpider(RssSpider):
    name = "healthline"
    start_urls = ["https://www.healthline.com/feed"]
    feed_name = "Healthline"
