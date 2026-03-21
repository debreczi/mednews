from ..rss_spider import RssSpider


class NapiEgeszsegSpider(RssSpider):
    name = "napi_egeszseg"
    start_urls = ["https://www.napi.hu/rss/egeszsegugy"]
    feed_name = "Napi.hu Egészségügy"
