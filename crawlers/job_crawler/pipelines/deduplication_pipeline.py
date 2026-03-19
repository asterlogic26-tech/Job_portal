import hashlib
import logging
import os

logger = logging.getLogger(__name__)


class DeduplicationPipeline:
    """Hash-based deduplication using Redis bloom filter."""

    def __init__(self):
        self._redis = None

    def open_spider(self, spider):
        try:
            import redis
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url)
            logger.info("Deduplication pipeline connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable for dedup: {e}")

    def process_item(self, item, spider):
        key = self._compute_key(item)

        if self._redis:
            try:
                redis_key = f"job_dedup:{key}"
                if self._redis.exists(redis_key):
                    from scrapy.exceptions import DropItem
                    raise DropItem(f"Duplicate job: {item.get('title')}")
                # Set with 7-day expiry
                self._redis.set(redis_key, "1", ex=604800)
            except Exception as e:
                if "DropItem" in type(e).__name__:
                    raise
                logger.error(f"Redis dedup error: {e}")

        return item

    def _compute_key(self, item) -> str:
        content = f"{item.get('title', '')}::{item.get('company_name', '')}::{item.get('source_url', '')}"
        return hashlib.md5(content.encode()).hexdigest()
