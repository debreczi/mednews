from ..rss_spider import RssSpider


class HealthcareItNewsSpider(RssSpider):
    name = "healthcare_it_news"
    start_urls = ["https://www.healthcareitnews.com/rss.xml"]
    feed_name = "Healthcare IT News"
