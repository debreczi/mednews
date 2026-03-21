from ..rss_spider import RssSpider


class HvgEgeszsegSpider(RssSpider):
    name = "hvg_egeszseg"
    start_urls = ["https://hvg.hu/rss/egeszseg"]
    feed_name = "HVG Egészség"
