from ..rss_spider import RssSpider


class WebbetegSpider(RssSpider):
    name = "webbeteg"
    start_urls = ["https://www.webbeteg.hu/rss/webbeteg.xml"]
    feed_name = "WEBBeteg"
