import logging
import scrapy
from abc import abstractmethod

logger = logging.getLogger(__name__)


class BaseJobSpider(scrapy.Spider):
    """
    Abstract base spider with:
    - Rate limiting enforcement
    - Block detection (via middleware)
    - robots.txt compliance (via ROBOTSTXT_OBEY=True in settings)
    """

    # Override in subclasses
    source_id = ""
    source_name = ""

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jobs_discovered = 0
        self.jobs_skipped = 0

    @abstractmethod
    def start_requests(self):
        """Override to generate initial requests."""
        ...

    def closed(self, reason):
        self.logger.info(
            f"Spider {self.name} closed: {reason}. "
            f"Discovered: {self.jobs_discovered}, Skipped: {self.jobs_skipped}"
        )
