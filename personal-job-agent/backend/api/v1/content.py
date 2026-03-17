import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.content import ContentRead, ContentGenerate, ContentUpdate, ContentListResponse
from backend.schemas.common import MessageResponse
from backend.services.content_service import ContentService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> ContentService:
    return ContentService(db)


@router.get("", response_model=ContentListResponse)
async def list_content(
    content_type: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ContentService = Depends(_svc),
):
    return await svc.list(user_id, content_type=content_type, status=status, page=page, page_size=page_size)


@router.post("/generate", response_model=ContentRead, status_code=201)
async def generate_content(
    payload: ContentGenerate,
    user_id: uuid.UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    svc = ContentService(db)
    return await svc.generate(user_id, payload)


@router.get("/{content_id}", response_model=ContentRead)
async def get_content(content_id: uuid.UUID, svc: ContentService = Depends(_svc)):
    item = await svc.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item


@router.patch("/{content_id}", response_model=ContentRead)
async def update_content(
    content_id: uuid.UUID,
    payload: ContentUpdate,
    svc: ContentService = Depends(_svc),
):
    item = await svc.update(content_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item


@router.post("/{content_id}/approve", response_model=ContentRead)
async def approve_content(content_id: uuid.UUID, svc: ContentService = Depends(_svc)):
    item = await svc.approve(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item


@router.delete("/{content_id}", response_model=MessageResponse)
async def delete_content(content_id: uuid.UUID, svc: ContentService = Depends(_svc)):
    await svc.delete(content_id)
    return MessageResponse(message="Content deleted")
