from ..rss_spider import RssSpider


class ModernHealthcareSpider(RssSpider):
    name = "modern_healthcare"
    start_urls = ["https://www.modernhealthcare.com/section/technology/rss"]
    feed_name = "Modern Healthcare IT"
