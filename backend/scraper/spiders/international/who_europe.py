from ..rss_spider import RssSpider


class WhoEuropeSpider(RssSpider):
    name = "who_europe"
    start_urls = ["https://www.euro.who.int/en/media-centre/news/rss.xml"]
    feed_name = "WHO Europe"
