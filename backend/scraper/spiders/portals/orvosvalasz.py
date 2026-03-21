from ..rss_spider import RssSpider


class OrvosvalaszSpider(RssSpider):
    name = "orvosvalasz"
    start_urls = ["https://www.orvosvalasz.hu/feed"]
    feed_name = "OrvosVálasz"
