from ..rss_spider import RssSpider


class BbcHealthSpider(RssSpider):
    name = "bbc_health"
    start_urls = ["https://www.bbc.com/news/health/rss.xml"]
    feed_name = "BBC Health"
