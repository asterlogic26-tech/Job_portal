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
    config = {}
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Could not load sources config: {e}")
        return {"discovered": 0, "errors": 1}

    sources_cfg = config.get("sources", {})
    total_discovered = 0
    errors = 0

    # ── RSS feeds ────────────────────────────────────────────
    rss_cfg = sources_cfg.get("rss_feeds", {})
    if rss_cfg.get("enabled"):
        for feed in rss_cfg.get("feeds", []):
            if not feed.get("enabled"):
                continue
            try:
                count = await _discover_from_rss_feed(feed)
                total_discovered += count
                logger.info(f"RSS [{feed.get('name')}]: {count} jobs")
            except Exception as e:
                logger.error(f"RSS [{feed.get('name')}] failed: {e}")
                errors += 1

    # ── ATS APIs ─────────────────────────────────────────────
    ats_cfg = sources_cfg.get("ats_apis", {})
    if ats_cfg.get("enabled"):
        gh_cfg = ats_cfg.get("providers", {}).get("greenhouse", {})
        if gh_cfg.get("enabled"):
            try:
                count = await _discover_greenhouse(gh_cfg.get("boards", []))
                total_discovered += count
                logger.info(f"Greenhouse: {count} jobs")
            except Exception as e:
                logger.error(f"Greenhouse failed: {e}")
                errors += 1

        lever_cfg = ats_cfg.get("providers", {}).get("lever", {})
        if lever_cfg.get("enabled"):
            try:
                count = await _discover_lever(lever_cfg.get("companies", []))
                total_discovered += count
                logger.info(f"Lever: {count} jobs")
            except Exception as e:
                logger.error(f"Lever failed: {e}")
                errors += 1

    # ── Direct APIs ──────────────────────────────────────────
    direct_cfg = sources_cfg.get("direct_apis", {})
    if direct_cfg.get("enabled"):
        remoteok_cfg = direct_cfg.get("providers", {}).get("remoteok", {})
        if remoteok_cfg.get("enabled"):
            try:
                count = await _discover_remoteok(remoteok_cfg)
                total_discovered += count
                logger.info(f"RemoteOK: {count} jobs")
            except Exception as e:
                logger.error(f"RemoteOK failed: {e}")
                errors += 1

        yc_cfg = direct_cfg.get("providers", {}).get("ycombinator", {})
        if yc_cfg.get("enabled"):
            try:
                count = await _discover_ycombinator()
                total_discovered += count
                logger.info(f"YCombinator: {count} jobs")
            except Exception as e:
                logger.error(f"YCombinator failed: {e}")
                errors += 1

    return {"discovered": total_discovered, "errors": errors}


async def _discover_from_rss_feed(feed: dict) -> int:
    """Discover jobs from a single RSS feed entry."""
    import feedparser
    import httpx

    url = feed.get("url", "")
    if not url:
        return 0

    count = 0
    async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": "PersonalJobAgent/1.0"}) as client:
        try:
            resp = await client.get(url)
            if resp.status_code in [403, 429, 503]:
                logger.warning(f"Blocked on {url} ({resp.status_code})")
                return 0

            parsed = feedparser.parse(resp.text)
            for entry in parsed.entries:
                await _store_raw_job({
                    "source": "rss_" + feed.get("name", "unknown").lower().replace(" ", "_"),
                    "source_url": entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "description_raw": entry.get("summary", ""),
                    "company_name": entry.get("author", "") or feed.get("name", ""),
                    "posted_at": entry.get("published", None),
                })
                count += 1
        except Exception as e:
            logger.error(f"RSS fetch error {url}: {e}")

    return count


async def _discover_greenhouse(boards: list) -> int:
    """Discover from Greenhouse public API."""
    from integrations.ats.greenhouse import GreenhouseClient

    client = GreenhouseClient()
    count = 0

    for slug in boards:
        try:
            jobs = await client.get_jobs(slug, limit=30)
            for job in jobs:
                normalized = client.normalize_job(job, slug.capitalize())
                await _store_raw_job(normalized)
                count += 1
        except Exception as e:
            logger.error(f"Greenhouse {slug}: {e}")

    return count


async def _discover_lever(companies: list) -> int:
    """Discover from Lever public API."""
    from integrations.ats.lever import LeverClient

    client = LeverClient()
    count = 0

    for slug in companies:
        try:
            jobs = await client.get_jobs(slug, limit=30)
            for job in jobs:
                normalized = client.normalize_job(job, slug.capitalize())
                await _store_raw_job(normalized)
                count += 1
        except Exception as e:
            logger.error(f"Lever {slug}: {e}")

    return count


async def _discover_remoteok(cfg: dict) -> int:
    """Discover from RemoteOK API."""
    import httpx

    tag_filter = cfg.get("tag_filter", [])
    count = 0
    try:
        async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": "PersonalJobAgent/1.0"}) as client:
            resp = await client.get("https://remoteok.com/api")
            if resp.status_code == 200:
                jobs = resp.json()
                for job in jobs[1:]:  # First item is metadata
                    if not isinstance(job, dict) or not job.get("position"):
                        continue
                    # Filter by tags if configured
                    job_tags = [t.lower() for t in job.get("tags", [])]
                    if tag_filter and not any(t in job_tags for t in tag_filter):
                        continue
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


async def _discover_ycombinator() -> int:
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
    normalize_job.delay(job_data)
