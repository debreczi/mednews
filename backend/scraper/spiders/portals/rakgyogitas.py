from ..rss_spider import RssSpider


class RakgyogitasSpider(RssSpider):
    name = "rakgyogitas"
    start_urls = ["https://rakgyogitas.hu/feed"]
    feed_name = "RákGyógyítás.hu"
