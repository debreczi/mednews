from ..rss_spider import RssSpider


class FarmakolagiaSpider(RssSpider):
    name = "farmakologia"
    start_urls = ["https://farmakologia.hu/feed"]
    feed_name = "Farmakológia.hu"
