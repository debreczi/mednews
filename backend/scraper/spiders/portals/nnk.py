from ..rss_spider import RssSpider


class NnkSpider(RssSpider):
    name = "nnk"
    start_urls = ["https://www.nnk.gov.hu/feed"]
    feed_name = "NNK"
