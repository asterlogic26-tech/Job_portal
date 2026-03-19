import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.job import JobRead, JobListResponse, JobFilter
from backend.schemas.common import MessageResponse
from backend.services.job_service import JobService

router = APIRouter()


def _job_service(db: AsyncSession = Depends(get_session)) -> JobService:
    return JobService(db)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    q: str | None = Query(None),
    remote_only: bool = Query(False),
    min_score: float | None = Query(None),
    seniority: str | None = Query(None),
    source: str | None = Query(None),
    saved_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: JobService = Depends(_job_service),
):
    f = JobFilter(
        q=q, remote_only=remote_only, min_score=min_score,
        seniority=seniority, source=source, saved_only=saved_only,
        page=page, page_size=page_size,
    )
    return await svc.list_jobs(user_id, f)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    svc: JobService = Depends(_job_service),
):
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/hide", response_model=MessageResponse)
async def hide_job(
    job_id: uuid.UUID,
    svc: JobService = Depends(_job_service),
):
    await svc.set_hidden(job_id, True)
    return MessageResponse(message="Job hidden")


@router.post("/{job_id}/unhide", response_model=MessageResponse)
async def unhide_job(
    job_id: uuid.UUID,
    svc: JobService = Depends(_job_service),
):
    await svc.set_hidden(job_id, False)
    return MessageResponse(message="Job unhidden")


@router.post("/{job_id}/save", response_model=MessageResponse)
async def save_job(
    job_id: uuid.UUID,
    svc: JobService = Depends(_job_service),
):
    await svc.set_saved(job_id, True)
    return MessageResponse(message="Job saved")


@router.delete("/{job_id}/save", response_model=MessageResponse)
async def unsave_job(
    job_id: uuid.UUID,
    svc: JobService = Depends(_job_service),
):
    await svc.set_saved(job_id, False)
    return MessageResponse(message="Job unsaved")


@router.post("/trigger-discovery", response_model=MessageResponse)
async def trigger_discovery():
    """Manually trigger the job discovery Celery task."""
    from workers.celery_app import celery_app
    celery_app.send_task(
        "workers.tasks.discovery_tasks.run_discovery",
        queue="discovery",
    )
    return MessageResponse(message="Job discovery triggered")


@router.post("/{job_id}/trigger-match", response_model=MessageResponse)
async def trigger_match(job_id: uuid.UUID):
    from workers.celery_app import celery_app
    celery_app.send_task(
        "workers.tasks.matching_tasks.compute_job_match",
        args=[str(job_id)],
        queue="matching",
    )
    return MessageResponse(message="Match computation triggered")
