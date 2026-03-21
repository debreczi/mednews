from ..rss_spider import RssSpider


class NatureMedicineSpider(RssSpider):
    name = "nature_medicine"
    start_urls = ["https://feeds.nature.com/nm/rss/current"]
    feed_name = "Nature Medicine"
