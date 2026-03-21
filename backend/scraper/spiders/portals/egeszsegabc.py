from ..rss_spider import RssSpider


class EgeszsegabcSpider(RssSpider):
    name = "egeszsegabc"
    start_urls = ["https://egeszsegabc.hu/feed"]
    feed_name = "Egészség ABC"
