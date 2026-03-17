import logging
import json
import os

logger = logging.getLogger(__name__)


class StoragePipeline:
    """Send discovered jobs to Celery normalization queue."""

    def __init__(self):
        self._redis = None

    def open_spider(self, spider):
        try:
            import redis
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url)
        except Exception as e:
            logger.warning(f"Redis unavailable for storage: {e}")

    def process_item(self, item, spider):
        item_dict = dict(item)

        if self._redis:
            try:
                # Push to normalization queue
                self._redis.rpush("raw_jobs_queue", json.dumps(item_dict, default=str))
                logger.debug(f"Queued job: {item.get('title')} from {item.get('source')}")
            except Exception as e:
                logger.error(f"Storage pipeline error: {e}")
        else:
            # Fallback: trigger Celery task directly
            try:
                from celery import Celery
                broker = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
                app = Celery(broker=broker)
                app.send_task("tasks.normalization_tasks.normalize_job", args=[item_dict])
            except Exception as e:
                logger.error(f"Celery dispatch failed: {e}")

        return item
