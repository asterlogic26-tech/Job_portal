"""
Daily rate limiter — Redis-backed.

Enforces hard daily caps on applies and LLM pipeline runs so costs
never exceed the configured budget.  Uses a Redis counter per calendar
day with a 25-hour expiry (1-hour grace to avoid midnight boundary issues).

Usage (in Celery tasks)::

    from workers.rate_limiter import check_apply_limit, check_pipeline_limit

    allowed, used, limit = check_apply_limit()
    if not allowed:
        logger.warning("Daily apply limit %d/%d reached — skipping", used, limit)
        return

Design: atomic INCR so concurrent workers never double-count.
        DECR is called on failure so the counter stays accurate.
"""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Tuple

logger = logging.getLogger(__name__)

# Redis keys — one counter per UTC day
_KEY_APPLIES   = "rate:daily_applies:{date}"
_KEY_PIPELINES = "rate:daily_pipelines:{date}"
_TTL_SECONDS   = 25 * 3600  # 25-hour expiry — avoids midnight edge cases

# ── Defaults (overridden by env vars / config) ────────────────────────────────
DEFAULT_MAX_DAILY_APPLIES   = 100
DEFAULT_MAX_DAILY_PIPELINES = 120   # slightly above applies to allow single-agent runs


def _today_key(pattern: str) -> str:
    return pattern.format(date=date.today().isoformat())


def _get_redis():
    """Get a Redis client (lazy import so workers don't need it at module load)."""
    import redis
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url, decode_responses=True, socket_timeout=3)


def _get_limit(env_var: str, default: int) -> int:
    try:
        return int(os.environ.get(env_var, default))
    except (ValueError, TypeError):
        return default


# ── Core helper ───────────────────────────────────────────────────────────────

def _check_and_increment(redis_key: str, limit: int) -> Tuple[bool, int, int]:
    """Atomically increment the counter and check against the limit.

    Returns:
        (allowed, current_count, limit)
        allowed=False means the limit was already reached before this call.
    """
    try:
        r = _get_redis()
        current = r.incr(redis_key)
        if current == 1:
            r.expire(redis_key, _TTL_SECONDS)

        if current > limit:
            # Rollback — this slot is beyond the limit
            r.decr(redis_key)
            return False, current - 1, limit

        return True, current, limit
    except Exception as exc:
        # Redis unavailable → fail OPEN (don't block the apply)
        logger.warning("Rate limiter Redis error (fail open): %s", exc)
        return True, 0, limit


def _get_count(redis_key: str) -> int:
    """Read the current counter without modifying it."""
    try:
        r = _get_redis()
        val = r.get(redis_key)
        return int(val) if val else 0
    except Exception as exc:
        logger.warning("Rate limiter read error: %s", exc)
        return 0


# ── Public API ────────────────────────────────────────────────────────────────

def check_apply_limit() -> Tuple[bool, int, int]:
    """Check and claim one apply slot for today.

    Returns:
        (allowed, used_after_this_call, daily_limit)

    If allowed=False the caller must NOT proceed with the apply.
    """
    limit = _get_limit("MAX_DAILY_APPLIES", DEFAULT_MAX_DAILY_APPLIES)
    return _check_and_increment(_today_key(_KEY_APPLIES), limit)


def check_pipeline_limit() -> Tuple[bool, int, int]:
    """Check and claim one LLM pipeline slot for today.

    Returns:
        (allowed, used_after_this_call, daily_limit)
    """
    limit = _get_limit("MAX_DAILY_PIPELINES", DEFAULT_MAX_DAILY_PIPELINES)
    return _check_and_increment(_today_key(_KEY_PIPELINES), limit)


def get_daily_usage() -> dict:
    """Return current daily usage counters — used by the dashboard API."""
    apply_limit    = _get_limit("MAX_DAILY_APPLIES",   DEFAULT_MAX_DAILY_APPLIES)
    pipeline_limit = _get_limit("MAX_DAILY_PIPELINES", DEFAULT_MAX_DAILY_PIPELINES)

    applies_used   = _get_count(_today_key(_KEY_APPLIES))
    pipelines_used = _get_count(_today_key(_KEY_PIPELINES))

    return {
        "date": date.today().isoformat(),
        "applies": {
            "used":      applies_used,
            "limit":     apply_limit,
            "remaining": max(0, apply_limit - applies_used),
            "pct":       round(applies_used / apply_limit * 100, 1) if apply_limit else 0,
        },
        "pipelines": {
            "used":      pipelines_used,
            "limit":     pipeline_limit,
            "remaining": max(0, pipeline_limit - pipelines_used),
            "pct":       round(pipelines_used / pipeline_limit * 100, 1) if pipeline_limit else 0,
        },
        "estimated_cost_usd": round(
            applies_used * 0.054,   # ~$0.054 per full apply pipeline
            2,
        ),
    }
