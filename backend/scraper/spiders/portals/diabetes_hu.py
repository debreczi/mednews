from ..rss_spider import RssSpider


class DiabetesHuSpider(RssSpider):
    name = "diabetes_hu"
    start_urls = ["https://diabetes.hu/feed"]
    feed_name = "Diabétesz Online"
