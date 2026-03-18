"""
API endpoints for the multi-agent system.

Endpoints:
  POST /agents/pipeline/{job_id}        Run full pipeline for a job
  POST /agents/pipeline/{job_id}/trigger Queue as async Celery task
  POST /agents/{agent_name}/run         Run single named agent
  GET  /agents/logs                     List agent execution logs
  GET  /agents/logs/{job_id}            Logs for a specific job
  GET  /agents/available                List available agent names
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session, get_user_id
from backend.services.agent_service import AgentService
from backend.schemas.agent import (
    AgentLogListResponse,
    AgentRunRequest,
    PipelineRunRequest,
    PipelineRunResponse,
    SingleAgentResponse,
)
from backend.schemas.common import MessageResponse

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> AgentService:
    return AgentService(db)


# ── Pipeline ──────────────────────────────────────────────────────────────────

@router.post("/pipeline/{job_id}", response_model=PipelineRunResponse)
async def run_pipeline(
    job_id: uuid.UUID,
    body: PipelineRunRequest = PipelineRunRequest(),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: AgentService = Depends(_svc),
):
    """Run the full multi-agent pipeline for the specified job.

    Executes all agents synchronously in the request and returns the
    complete pipeline result including every agent's output.
    """
    try:
        result = await svc.run_pipeline(
            job_id=job_id,
            user_id=user_id,
            additional_context=body.additional_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return PipelineRunResponse(
        pipeline_run_id=result["pipeline_run_id"],
        job_id=result.get("job_id"),
        success=result["success"],
        agent_results=result["agent_results"],
        agent_logs_saved=result.get("agent_logs_saved", 0),
    )


@router.post("/pipeline/{job_id}/trigger", response_model=MessageResponse)
async def trigger_pipeline(
    job_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
):
    """Queue the agent pipeline as an async Celery task.

    Returns immediately; check logs once the task completes.
    """
    from workers.celery_app import celery_app
    celery_app.send_task(
        "workers.tasks.agent_tasks.run_agent_pipeline",
        args=[str(job_id)],
        queue="default",
    )
    return MessageResponse(message=f"Agent pipeline queued for job {job_id}")


# ── Single agent ──────────────────────────────────────────────────────────────

@router.post("/{agent_name}/run", response_model=SingleAgentResponse)
async def run_single_agent(
    agent_name: str,
    body: AgentRunRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    svc: AgentService = Depends(_svc),
):
    """Run a single named agent with the supplied input_data.

    Useful for testing individual agents or triggering on-demand
    generations (e.g. a fresh LinkedIn post).
    """
    from agents.orchestrator import AgentOrchestrator
    if agent_name not in AgentOrchestrator.available_agents():
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {AgentOrchestrator.available_agents()}",
        )

    output = await svc.run_single_agent(
        agent_name=agent_name,
        input_data=body.input_data,
        user_id=user_id,
    )
    error = output.get("error")
    return SingleAgentResponse(
        agent_name=agent_name,
        output=output,
        success=error is None,
        duration_ms=0.0,
        error=error,
    )


# ── Logs ──────────────────────────────────────────────────────────────────────

@router.get("/logs", response_model=AgentLogListResponse)
async def list_logs(
    agent_name: Optional[str] = Query(None),
    pipeline_run_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    svc: AgentService = Depends(_svc),
):
    """List agent execution logs with optional filters."""
    return await svc.list_logs(
        agent_name=agent_name,
        pipeline_run_id=pipeline_run_id,
        page=page,
        page_size=page_size,
    )


@router.get("/logs/job/{job_id}", response_model=AgentLogListResponse)
async def logs_for_job(
    job_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    svc: AgentService = Depends(_svc),
):
    """Return all agent logs for a specific job across all pipeline runs."""
    return await svc.list_logs(job_id=job_id, page=page, page_size=page_size)


# ── Daily limits ─────────────────────────────────────────────────────────────

@router.get("/limits")
async def get_daily_limits():
    """Return today's apply and pipeline usage vs configured limits.

    Use this on the dashboard to show how many auto-applies remain today
    and the estimated API cost so far.

    Example response::

        {
          "date": "2026-03-18",
          "applies":   {"used": 12, "limit": 100, "remaining": 88, "pct": 12.0},
          "pipelines": {"used": 14, "limit": 120, "remaining": 106, "pct": 11.7},
          "estimated_cost_usd": 0.65
        }
    """
    from workers.rate_limiter import get_daily_usage
    return get_daily_usage()


# ── Discovery ─────────────────────────────────────────────────────────────────

@router.get("/available")
async def list_available_agents():
    """Return the names and pipeline order of all registered agents."""
    from agents.orchestrator import AgentOrchestrator
    return {
        "agents": AgentOrchestrator.available_agents(),
        "pipeline_sequence": AgentOrchestrator.pipeline_sequence(),
    }
