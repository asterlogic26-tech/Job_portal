import logging
import asyncio
import os


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="workers.tasks.discovery_tasks.run_discovery",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_discovery(self):
    """Run job discovery across all enabled sources."""
    logger.info("Starting job discovery run...")
    try:
        result = asyncio.run(_run_discovery_async())
        logger.info(f"Discovery complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"Discovery failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


async def _run_discovery_async():
    """Async implementation of job discovery."""
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent / "config" / "sources.yml"
    sources = []
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            sources = config.get("sources", [])
    except Exception as e:
        logger.error(f"Could not load sources config: {e}")
        return {"discovered": 0, "errors": 1}

    total_discovered = 0
    errors = 0

    for source in sources:
        if not source.get("enabled"):
            continue

        source_id = source.get("id")
        source_type = source.get("type")

        try:
            if source_type == "rss":
                count = await _discover_from_rss(source)
            elif source_type == "api":
                count = await _discover_from_api(source)
            else:
                count = 0
            total_discovered += count
            logger.info(f"Source {source_id}: discovered {count} jobs")
        except Exception as e:
            logger.error(f"Source {source_id} failed: {e}")
            errors += 1

    return {"discovered": total_discovered, "errors": errors}


async def _discover_from_rss(source: dict) -> int:
    """Discover jobs from RSS feeds."""
    import feedparser
    import httpx
    from datetime import datetime, timezone

    feed_urls = source.get("feed_urls", [])
    count = 0

    async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": "PersonalJobAgent/1.0"}) as client:
        for url in feed_urls:
            try:
                resp = await client.get(url)
                if resp.status_code in [403, 429, 503]:
                    logger.warning(f"Blocked on {url} ({resp.status_code}) — creating manual task")
                    await _create_manual_task_for_block(source["id"], url, resp.status_code)
                    continue

                feed = feedparser.parse(resp.text)
                for entry in feed.entries:
                    await _store_raw_job({
                        "source": source["id"],
                        "source_url": entry.get("link", ""),
                        "title": entry.get("title", ""),
                        "description_raw": entry.get("summary", ""),
                        "company_name": _extract_company_from_feed(entry, source),
                        "posted_at": entry.get("published", None),
                    })
                    count += 1
            except Exception as e:
                logger.error(f"RSS fetch error {url}: {e}")

    return count


async def _discover_from_api(source: dict) -> int:
    """Discover jobs from official APIs."""
    source_id = source.get("id")

    if source_id == "greenhouse_api":
        return await _discover_greenhouse(source)
    elif source_id == "lever_api":
        return await _discover_lever(source)
    elif source_id == "remoteok_api":
        return await _discover_remoteok(source)
    elif source_id == "ycombinator_jobs":
        return await _discover_ycombinator(source)
    return 0


async def _discover_greenhouse(source: dict) -> int:
    """Discover from Greenhouse public API."""
    import httpx
    from integrations.ats.greenhouse import GreenhouseClient

    # List of companies to check (would be configurable in production)
    companies = [
        ("airbnb", "Airbnb"),
        ("stripe", "Stripe"),
        ("notion", "Notion"),
        ("figma", "Figma"),
        ("linear", "Linear"),
    ]

    client = GreenhouseClient()
    count = 0

    for slug, name in companies:
        try:
            jobs = await client.get_jobs(slug, limit=30)
            for job in jobs:
                normalized = client.normalize_job(job, name)
                await _store_raw_job(normalized)
                count += 1
        except Exception as e:
            logger.error(f"Greenhouse {slug}: {e}")

    return count


async def _discover_lever(source: dict) -> int:
    """Discover from Lever public API."""
    from integrations.ats.lever import LeverClient

    companies = [
        ("netflix", "Netflix"),
        ("coinbase", "Coinbase"),
        ("pinterest", "Pinterest"),
    ]

    client = LeverClient()
    count = 0

    for slug, name in companies:
        try:
            jobs = await client.get_jobs(slug, limit=30)
            for job in jobs:
                normalized = client.normalize_job(job, name)
                await _store_raw_job(normalized)
                count += 1
        except Exception as e:
            logger.error(f"Lever {slug}: {e}")

    return count


async def _discover_remoteok(source: dict) -> int:
    """Discover from RemoteOK API."""
    import httpx

    count = 0
    try:
        async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": "PersonalJobAgent/1.0"}) as client:
            resp = await client.get("https://remoteok.com/api")
            if resp.status_code == 200:
                jobs = resp.json()
                for job in jobs[1:]:  # First item is metadata
                    if isinstance(job, dict) and job.get("position"):
                        await _store_raw_job({
                            "source": "remoteok_api",
                            "external_id": str(job.get("id", "")),
                            "title": job.get("position", ""),
                            "company_name": job.get("company", ""),
                            "description_raw": job.get("description", ""),
                            "source_url": job.get("url", ""),
                            "remote_policy": "remote",
                            "posted_at": None,
                            "apply_url": job.get("apply_url", job.get("url", "")),
                            "skills_required": [{"name": t} for t in job.get("tags", [])],
                        })
                        count += 1
    except Exception as e:
        logger.error(f"RemoteOK API error: {e}")
    return count


async def _discover_ycombinator(source: dict) -> int:
    """Discover from Y Combinator Work at a Startup."""
    import httpx

    count = 0
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                "https://api.workatastartup.com/companies",
                headers={"User-Agent": "PersonalJobAgent/1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                companies = data.get("companies", [])
                for company in companies[:50]:
                    for job in company.get("jobs", []):
                        await _store_raw_job({
                            "source": "ycombinator_jobs",
                            "external_id": str(job.get("id", "")),
                            "title": job.get("title", ""),
                            "company_name": company.get("name", ""),
                            "description_raw": job.get("description", ""),
                            "source_url": f"https://www.workatastartup.com/jobs/{job.get('id','')}",
                            "remote_policy": "remote" if job.get("remote", False) else "onsite",
                            "location": job.get("location", ""),
                        })
                        count += 1
    except Exception as e:
        logger.error(f"YC API error: {e}")
    return count


async def _store_raw_job(job_data: dict):
    """Store a discovered job and trigger normalization."""
    from workers.tasks.normalization_tasks import normalize_job
    # Trigger normalization asynchronously
    normalize_job.delay(job_data)


async def _create_manual_task_for_block(source_id: str, url: str, status_code: int):
    """Create a manual task when a source blocks the crawler."""
    # Use sync DB session for Celery context
    from db_utils import get_sync_session
    try:
        with get_sync_session() as session:
            from sqlalchemy import text
            import uuid
            session.execute(
                text("""
                INSERT INTO manual_tasks (id, source_service, category, priority, title, description, action_url, status, context_data, created_at, updated_at)
                VALUES (:id, :source, :category, :priority, :title, :desc, :url, 'pending', :ctx, NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "source": source_id,
                    "category": "verification_needed",
                    "priority": "medium",
                    "title": f"Manual review needed: {source_id}",
                    "desc": f"Source {source_id} returned {status_code}. Manual verification may be needed.",
                    "url": url,
                    "ctx": '{"status_code": ' + str(status_code) + '}',
                },
            )
            session.commit()
    except Exception as e:
        logger.error(f"Could not create manual task: {e}")


def _extract_company_from_feed(entry, source) -> str:
    """Try to extract company name from feed entry."""
    return entry.get("author", "") or entry.get("company", "") or source.get("name", "")
