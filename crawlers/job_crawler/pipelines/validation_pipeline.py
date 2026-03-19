import logging
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["title", "source", "source_url"]


class ValidationPipeline:
    """Validate required fields and drop malformed items."""

    def process_item(self, item, spider):
        for field in REQUIRED_FIELDS:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field} in {dict(item)}")

        if len(item.get("title", "")) < 3:
            raise DropItem(f"Title too short: {item.get('title')}")

        return item
