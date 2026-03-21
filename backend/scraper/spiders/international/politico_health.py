from ..rss_spider import RssSpider


class PoliticoHealthSpider(RssSpider):
    name = "politico_health"
    start_urls = ["https://www.politico.eu/section/health-care/feed/"]
    feed_name = "Politico EU Health"
