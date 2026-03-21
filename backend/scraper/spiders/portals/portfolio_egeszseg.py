from ..rss_spider import RssSpider


class PortfolioEgeszsegSpider(RssSpider):
    name = "portfolio_egeszseg"
    start_urls = ["https://www.portfolio.hu/rss/egeszsegugy.xml"]
    feed_name = "Portfolio Egészségügy"
