import uuid
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.profile import ProfileRead, ProfileUpdate, ProfileHealthRead
from backend.schemas.common import MessageResponse
from backend.services.profile_service import ProfileService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> ProfileService:
    return ProfileService(db)


@router.get("", response_model=ProfileRead)
async def get_profile(
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ProfileService = Depends(_svc),
):
    return await svc.get_or_create(user_id)


@router.patch("", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ProfileService = Depends(_svc),
):
    return await svc.update(user_id, payload)


@router.get("/health", response_model=ProfileHealthRead)
async def get_health(
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ProfileService = Depends(_svc),
):
    return await svc.get_health(user_id)


@router.post("/upload-resume", response_model=MessageResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ProfileService = Depends(_svc),
):
    url = await svc.upload_resume(user_id, file)
    return MessageResponse(message=f"Resume uploaded: {url}")


@router.post("/refresh-embedding", response_model=MessageResponse)
async def refresh_embedding(
    user_id: uuid.UUID = Depends(get_user_id),
    svc: ProfileService = Depends(_svc),
):
    await svc.refresh_embedding(user_id)
    return MessageResponse(message="Profile embedding refreshed")
