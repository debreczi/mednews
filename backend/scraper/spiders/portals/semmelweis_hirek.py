from ..rss_spider import RssSpider


class SemmelweisHirekSpider(RssSpider):
    name = "semmelweis_hirek"
    start_urls = ["https://semmelweis.hu/hirek/feed"]
    feed_name = "Semmelweis Hírek"
