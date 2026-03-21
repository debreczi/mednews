from ..rss_spider import RssSpider


class AntszSpider(RssSpider):
    name = "antsz"
    start_urls = ["https://www.antsz.hu/felso_menu/sajtoszoba/rss.xml"]
    feed_name = "ANTSZ"
