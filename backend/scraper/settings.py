"""Scrapy project settings."""

BOT_NAME = "mednews"

SPIDER_MODULES = ["backend.scraper.spiders"]
NEWSPIDER_MODULE = "backend.scraper.spiders"

# Pipelines (order matters)
ITEM_PIPELINES = {
    "backend.scraper.pipelines.DuplicateFilterPipeline": 100,
    "backend.scraper.pipelines.ScoreFilterPipeline": 200,
    "backend.scraper.pipelines.EnrichmentPipeline": 300,
    "backend.scraper.pipelines.DatabasePipeline": 400,
}

# Polite crawling
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# User agent rotation
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Playwright (opt-in per-request via meta={"playwright": True})
# Not applied globally — RSS spiders use standard HTTP, no browser needed
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# Feed exports
FEEDS = {}

# Retry
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
