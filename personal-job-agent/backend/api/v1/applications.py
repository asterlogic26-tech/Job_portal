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


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    status: str | None = Query(None),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.list(user_id, status_filter=status)


@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application(
    payload: ApplicationCreate,
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.create(user_id, payload)


@router.get("/{app_id}", response_model=ApplicationRead)
async def get_application(
    app_id: uuid.UUID,
    svc: ApplicationService = Depends(_svc),
):
    app = await svc.get(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


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
    app = await svc.update_status(app_id, payload.status)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.delete("/{app_id}", response_model=MessageResponse)
async def delete_application(
    app_id: uuid.UUID,
    svc: ApplicationService = Depends(_svc),
):
    await svc.delete(app_id)
    return MessageResponse(message="Application deleted")
