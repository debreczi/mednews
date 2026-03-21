from ..rss_spider import RssSpider


class OgyeiSpider(RssSpider):
    name = "ogyei"
    start_urls = ["https://ogyei.gov.hu/feed"]
    feed_name = "OGYÉI"
