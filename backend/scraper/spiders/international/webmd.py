from ..rss_spider import RssSpider


class WebmdSpider(RssSpider):
    name = "webmd"
    start_urls = ["https://www.webmd.com/rss"]
    feed_name = "WebMD"
