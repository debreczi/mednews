from ..rss_spider import RssSpider


class ScienceDailySpider(RssSpider):
    name = "science_daily"
    start_urls = ["https://www.sciencedaily.com/feeds/health_medicine.xml"]
    feed_name = "Science Daily Health"
