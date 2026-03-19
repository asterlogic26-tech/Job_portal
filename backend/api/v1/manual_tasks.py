import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.manual_task import ManualTaskRead, ManualTaskResolve, ManualTaskListResponse
from backend.schemas.common import MessageResponse
from backend.services.manual_task_service import ManualTaskService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> ManualTaskService:
    return ManualTaskService(db)


@router.get("", response_model=ManualTaskListResponse)
async def list_tasks(
    status: str | None = Query(None),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ManualTaskService = Depends(_svc),
):
    return await svc.list(user_id, status_filter=status)


@router.get("/{task_id}", response_model=ManualTaskRead)
async def get_task(task_id: uuid.UUID, svc: ManualTaskService = Depends(_svc)):
    task = await svc.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/start", response_model=ManualTaskRead)
async def start_task(task_id: uuid.UUID, svc: ManualTaskService = Depends(_svc)):
    task = await svc.update_status(task_id, "in_progress")
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/resolve", response_model=ManualTaskRead)
async def resolve_task(
    task_id: uuid.UUID,
    payload: ManualTaskResolve,
    svc: ManualTaskService = Depends(_svc),
):
    task = await svc.resolve(task_id, payload.completion_notes)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/skip", response_model=ManualTaskRead)
async def skip_task(task_id: uuid.UUID, svc: ManualTaskService = Depends(_svc)):
    task = await svc.update_status(task_id, "skipped")
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
