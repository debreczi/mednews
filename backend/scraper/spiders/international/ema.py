from ..rss_spider import RssSpider


class EmaSpider(RssSpider):
    name = "ema"
    start_urls = ["https://www.ema.europa.eu/en/news/rss.xml"]
    feed_name = "EMA News"
