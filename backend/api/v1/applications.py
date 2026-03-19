import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session, get_user_id
from backend.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationRead,
    ApplicationStatusUpdate,
)
from backend.schemas.common import MessageResponse
from backend.services.application_service import ApplicationService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> ApplicationService:
    return ApplicationService(db)


# ── List / get ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    status: str | None = Query(None),
    auto_applied_only: bool = Query(False),
    blocked_only: bool = Query(False),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.list(
        user_id,
        status_filter=status,
        auto_applied_only=auto_applied_only,
        blocked_only=blocked_only,
    )


@router.get("/stats")
async def application_stats(
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ApplicationService = Depends(_svc),
):
    """Return aggregate counts by status — used by the dashboard."""
    return await svc.get_stats(user_id)


@router.get("/{app_id}", response_model=ApplicationRead)
async def get_application(
    app_id: uuid.UUID,
    svc: ApplicationService = Depends(_svc),
):
    app = await svc.get(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


# ── Create / update ───────────────────────────────────────────────────────────

@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application(
    payload: ApplicationCreate,
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.create(user_id, payload)


@router.patch("/{app_id}", response_model=ApplicationRead)
async def update_application(
    app_id: uuid.UUID,
    payload: ApplicationUpdate,
    svc: ApplicationService = Depends(_svc),
):
    app = await svc.update(app_id, payload)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{app_id}/status", response_model=ApplicationRead)
async def update_status(
    app_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    svc: ApplicationService = Depends(_svc),
):
    app = await svc.update_status(app_id, payload.status, payload.note)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


# ── Auto-apply ────────────────────────────────────────────────────────────────

@router.post("/job/{job_id}/auto-apply", response_model=MessageResponse)
async def trigger_auto_apply(
    job_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ApplicationService = Depends(_svc),
):
    """Queue an auto-apply Celery task for the given job."""
    task_id = await svc.trigger_auto_apply(job_id)
    return MessageResponse(message=f"Auto-apply queued (task {task_id})")


@router.post("/{app_id}/mark-applied", response_model=ApplicationRead)
async def mark_manually_applied(
    app_id: uuid.UUID,
    svc: ApplicationService = Depends(_svc),
):
    """Mark a blocked application as manually applied by the user."""
    app = await svc.mark_manually_applied(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{app_id}", response_model=MessageResponse)
async def delete_application(
    app_id: uuid.UUID,
    svc: ApplicationService = Depends(_svc),
):
    await svc.delete(app_id)
    return MessageResponse(message="Application deleted")
