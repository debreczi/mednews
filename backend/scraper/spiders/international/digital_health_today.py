from ..rss_spider import RssSpider


class DigitalHealthTodaySpider(RssSpider):
    name = "digital_health_today"
    start_urls = ["https://digitalhealth.today/feed/"]
    feed_name = "Digital Health Today"
