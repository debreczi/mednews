from ..rss_spider import RssSpider


class StatNewsSpider(RssSpider):
    name = "stat_news"
    start_urls = ["https://www.statnews.com/feed/"]
    feed_name = "STAT News"
