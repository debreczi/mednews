from ..rss_spider import RssSpider


class MedicalNewsTodaySpider(RssSpider):
    name = "medical_news_today"
    start_urls = ["https://www.medicalnewstoday.com/feed"]
    feed_name = "Medical News Today"
