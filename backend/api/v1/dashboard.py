import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.dashboard import DashboardSummary
from backend.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    user_id: uuid.UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    svc = DashboardService(db)
    return await svc.get_summary(user_id)
