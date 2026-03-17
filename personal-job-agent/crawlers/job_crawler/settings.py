import os

BOT_NAME = "job_crawler"
SPIDER_MODULES = ["job_crawler.spiders"]
NEWSPIDER_MODULE = "job_crawler.spiders"

# Respect robots.txt
ROBOTSTXT_OBEY = True

# Rate limiting
DOWNLOAD_DELAY = float(os.environ.get("SCRAPER_REQUEST_DELAY", "2.0"))
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = int(os.environ.get("SCRAPER_CONCURRENT_REQUESTS", "4"))
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# User agent
USER_AGENT = os.environ.get(
    "SCRAPER_USER_AGENT",
    "PersonalJobAgent/1.0 (personal job search automation; not commercial)"
)

# Pipelines
ITEM_PIPELINES = {
    "job_crawler.pipelines.validation_pipeline.ValidationPipeline": 100,
    "job_crawler.pipelines.deduplication_pipeline.DeduplicationPipeline": 200,
    "job_crawler.pipelines.storage_pipeline.StoragePipeline": 300,
}

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    "job_crawler.middlewares.BlockDetectorMiddleware": 100,
}

# Extensions
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
}

# Redis for deduplication
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

# Auto-throttle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# HTTP caching
HTTPCACHE_ENABLED = False

LOG_LEVEL = "INFO"
FEEDS = {}
