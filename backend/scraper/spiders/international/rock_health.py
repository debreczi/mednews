from ..rss_spider import RssSpider


class RockHealthSpider(RssSpider):
    name = "rock_health"
    start_urls = ["https://rockhealth.com/feed/"]
    feed_name = "Rock Health"
