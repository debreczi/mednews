from ..rss_spider import RssSpider


class TelexEgeszsegSpider(RssSpider):
    name = "telex_egeszseg"
    start_urls = ["https://telex.hu/rss/egeszseg"]
    feed_name = "Telex Egészség"
