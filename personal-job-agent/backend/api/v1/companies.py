import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.company import CompanyRead, CompanyListResponse, CompanySignalRead
from backend.schemas.common import MessageResponse
from backend.services.company_service import CompanyService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> CompanyService:
    return CompanyService(db)


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    watched_only: bool = Query(False),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: CompanyService = Depends(_svc),
):
    return await svc.list(watched_only=watched_only, q=q, page=page, page_size=page_size)


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: uuid.UUID,
    svc: CompanyService = Depends(_svc),
):
    company = await svc.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/{company_id}/watch", response_model=MessageResponse)
async def watch_company(company_id: uuid.UUID, svc: CompanyService = Depends(_svc)):
    await svc.set_watched(company_id, True)
    return MessageResponse(message="Company added to watchlist")


@router.delete("/{company_id}/watch", response_model=MessageResponse)
async def unwatch_company(company_id: uuid.UUID, svc: CompanyService = Depends(_svc)):
    await svc.set_watched(company_id, False)
    return MessageResponse(message="Company removed from watchlist")


@router.get("/{company_id}/signals", response_model=list[CompanySignalRead])
async def get_company_signals(company_id: uuid.UUID, svc: CompanyService = Depends(_svc)):
    return await svc.get_signals(company_id)


@router.post("/{company_id}/trigger-radar", response_model=MessageResponse)
async def trigger_radar(company_id: uuid.UUID):
    from workers.celery_app import celery_app
    celery_app.send_task(
        "workers.tasks.company_radar_tasks.scan_company_signals",
        args=[str(company_id)],
        queue="radar",
    )
    return MessageResponse(message="Radar scan triggered")
