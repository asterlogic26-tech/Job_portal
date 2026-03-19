import logging
import asyncio
import os
import json
import uuid


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.company_radar_tasks.scan_company_signals")
def scan_company_signals():
    """Scan company signals: funding news and job velocity."""
    asyncio.run(_scan_async())


async def _scan_async():
    import yaml
    from pathlib import Path
    from engines.company_radar.signal_collector import SignalCollector
    from db_utils import get_sync_session
    from sqlalchemy import text

    collector = SignalCollector()

    config_path = Path(__file__).parent.parent.parent / "config" / "sources.yml"
    news_sources = []
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            news_sources = config.get("news_sources", [])
    except Exception as e:
        logger.error(f"Could not load news sources: {e}")

    # Collect funding signals
    funding_signals = await collector.collect_funding_signals(news_sources)
    logger.info(f"Found {len(funding_signals)} funding signals")

    with get_sync_session() as session:
        # Update job posting counts for companies
        companies = session.execute(
            text("SELECT id, name, job_posting_count_30d, job_posting_count_90d FROM companies")
        ).fetchall()

        for company_id, name, count_30d, count_90d in companies:
            # Compute job velocity
            velocity = await collector.collect_job_velocity(str(company_id), count_30d or 0, count_90d or 0)

            # Get relevant funding signals for this company
            company_signals = [
                s for s in funding_signals
                if name.lower() in s.get("headline", "").lower()
            ]

            # Compute hiring score
            all_signals = company_signals + [velocity]
            hiring_score = collector.compute_hiring_score(all_signals, count_30d or 0)

            # Update company
            session.execute(
                text("""
                UPDATE companies
                SET hiring_score = :score, updated_at = NOW()
                WHERE id = :id
                """),
                {"score": hiring_score, "id": str(company_id)},
            )

            # Store new signals
            for signal in company_signals:
                session.execute(
                    text("""
                    INSERT INTO company_signals (id, company_id, signal_type, source, headline, url, created_at, updated_at)
                    VALUES (:id, :company_id, :type, :source, :headline, :url, NOW(), NOW())
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "company_id": str(company_id),
                        "type": signal.get("signal_type", "funding"),
                        "source": signal.get("source", ""),
                        "headline": signal.get("headline", "")[:500],
                        "url": signal.get("url", ""),
                    },
                )

        session.commit()

    logger.info("Company radar scan complete")
