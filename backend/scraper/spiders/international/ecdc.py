from ..rss_spider import RssSpider


class EcdcSpider(RssSpider):
    name = "ecdc"
    start_urls = ["https://www.ecdc.europa.eu/en/news-events/rss.xml"]
    feed_name = "ECDC"
