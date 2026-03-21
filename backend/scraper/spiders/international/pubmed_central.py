from ..rss_spider import RssSpider


class PubmedCentralSpider(RssSpider):
    name = "pubmed_central"
    start_urls = ["https://www.ncbi.nlm.nih.gov/news/rss"]
    feed_name = "PubMed Central News"
