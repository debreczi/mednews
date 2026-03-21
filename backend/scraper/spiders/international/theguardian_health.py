from ..rss_spider import RssSpider


class TheGuardianHealthSpider(RssSpider):
    name = "theguardian_health"
    start_urls = ["https://www.theguardian.com/science/medical-research/rss"]
    feed_name = "The Guardian Health"
