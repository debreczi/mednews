from ..rss_spider import RssSpider


class G7EgeszsegSpider(RssSpider):
    name = "g7_egeszseg"
    start_urls = ["https://g7.hu/feed/?cat=egeszseg"]
    feed_name = "G7 Egészség"
