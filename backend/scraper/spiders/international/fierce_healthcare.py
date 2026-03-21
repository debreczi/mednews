from ..rss_spider import RssSpider


class FierceHealthcareSpider(RssSpider):
    name = "fierce_healthcare"
    start_urls = ["https://www.fiercehealthcare.com/rss/xml"]
    feed_name = "Fierce Healthcare"
