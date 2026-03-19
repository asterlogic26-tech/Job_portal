import logging
from scrapy import signals
from scrapy.http import Response

logger = logging.getLogger(__name__)

BLOCK_STATUS_CODES = {403, 429, 503, 401}
CAPTCHA_INDICATORS = [
    "captcha", "verify you are human", "access denied", "bot detected",
    "are you a robot", "security check", "ddos-guard", "cloudflare"
]


class BlockDetectorMiddleware:
    """
    Middleware that detects CAPTCHA and anti-bot blocks.
    When detected: creates a manual task instead of bypassing.
    This is a core ethical constraint — never bypass, always escalate.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        logger.info(f"Spider opened: {spider.name}")

    def process_response(self, request, response: Response, spider):
        # Check status code
        if response.status in BLOCK_STATUS_CODES:
            logger.warning(
                f"Blocked by {request.url} (status {response.status}). "
                f"Creating manual task. NOT bypassing."
            )
            self._create_manual_task(request.url, f"HTTP {response.status}", spider)
            # Return empty response instead of proceeding
            return response.replace(status=200, body=b"")

        # Check for CAPTCHA in content
        body_lower = response.text.lower() if response.text else ""
        for indicator in CAPTCHA_INDICATORS:
            if indicator in body_lower:
                logger.warning(
                    f"CAPTCHA/bot detection at {request.url}. "
                    f"Creating manual task. NOT bypassing."
                )
                self._create_manual_task(request.url, "CAPTCHA detected", spider)
                return response.replace(status=200, body=b"")

        return response

    def process_exception(self, request, exception, spider):
        logger.error(f"Request exception for {request.url}: {exception}")
        return None

    def _create_manual_task(self, url: str, reason: str, spider):
        """Create a manual task record in the database."""
        try:
            import redis
            import json
            import os
            r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
            task = {
                "source": spider.name,
                "url": url,
                "reason": reason,
                "action": "create_manual_task",
                "category": "verification_needed",
            }
            r.lpush("manual_task_queue", json.dumps(task))
        except Exception as e:
            logger.error(f"Could not queue manual task: {e}")
