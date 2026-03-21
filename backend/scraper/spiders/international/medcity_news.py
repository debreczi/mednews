from ..rss_spider import RssSpider


class MedcityNewsSpider(RssSpider):
    name = "medcity_news"
    start_urls = ["https://medcitynews.com/feed/"]
    feed_name = "MedCity News"
