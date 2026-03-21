from ..rss_spider import RssSpider


class MagyarorvosSpider(RssSpider):
    name = "magyarorvos"
    start_urls = ["https://www.magyarorvos.hu/rss.xml"]
    feed_name = "Magyar Orvos"
