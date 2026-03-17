"""
Celery tasks for the multi-agent pipeline.

These tasks allow the agent orchestrator to run asynchronously in the
background without blocking an API request.  Each task wraps the async
orchestrator with ``asyncio.run()`` (same pattern as matching_tasks.py).
"""
import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

SINGLE_USER_ID = "00000000-0000-0000-0000-000000000001"


@celery_app.task(
    name="workers.tasks.agent_tasks.run_agent_pipeline",
    bind=True,
)
def run_agent_pipeline(self, job_id: str):
    """Run the full multi-agent pipeline for a single job.

    Loads job + profile from the DB via a sync session, runs the
    orchestrator in an async event loop, and persists all agent logs.
    """
    try:
        asyncio.run(_run_pipeline_async(job_id))
    except Exception as exc:
        logger.error("Agent pipeline failed for job %s: %s", job_id, exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(
    name="workers.tasks.agent_tasks.run_single_agent",
    bind=True,
)
def run_single_agent(self, agent_name: str, input_data: dict, job_id: str | None = None):
    """Run a single named agent asynchronously."""
    try:
        asyncio.run(_run_single_async(agent_name, input_data, job_id))
    except Exception as exc:
        logger.error("Agent '%s' task failed: %s", agent_name, exc)
        raise self.retry(exc=exc, countdown=30)


# ── Async implementations ──────────────────────────────────────────────────────

async def _run_pipeline_async(job_id: str):
    """Full async pipeline implementation for the Celery task."""
    import uuid
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    import os

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent",
    )
    # Ensure asyncpg prefix
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        from backend.services.agent_service import AgentService
        svc = AgentService(db)
        try:
            result = await svc.run_pipeline(
                job_id=uuid.UUID(job_id),
                user_id=uuid.UUID(SINGLE_USER_ID),
            )
            logger.info(
                "Agent pipeline complete for job %s — run_id=%s, success=%s, logs=%d",
                job_id,
                result.get("pipeline_run_id"),
                result.get("success"),
                result.get("agent_logs_saved", 0),
            )
        except Exception as exc:
            logger.exception("Agent pipeline error for job %s", job_id)
            raise

    await engine.dispose()


async def _run_single_async(agent_name: str, input_data: dict, job_id: str | None):
    """Single agent async implementation for the Celery task."""
    import uuid
    from agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()
    output = await orchestrator.run_single(agent_name, input_data)
    logger.info(
        "Agent '%s' task complete for job %s — success=%s",
        agent_name,
        job_id,
        "error" not in output,
    )
    return output
