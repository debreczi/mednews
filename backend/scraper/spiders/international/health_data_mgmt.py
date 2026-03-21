from ..rss_spider import RssSpider


class HealthDataMgmtSpider(RssSpider):
    name = "health_data_mgmt"
    start_urls = ["https://www.healthdatamanagement.com/feed"]
    feed_name = "Health Data Management"
