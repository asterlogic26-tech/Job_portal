from __future__ import annotations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from backend.models.company import Company
from backend.models.company_signal import CompanySignal
from backend.schemas.company import CompanyRead, CompanyListResponse, CompanySignalRead


class CompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        watched_only: bool = False,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CompanyListResponse:
        stmt = select(Company).options(selectinload(Company.signals))

        if watched_only:
            stmt = stmt.where(Company.is_watched == True)
        if q:
            stmt = stmt.where(Company.name.ilike(f"%{q}%"))

        count = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = stmt.order_by(Company.hiring_score.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        companies = result.scalars().all()

        return CompanyListResponse(
            items=[CompanyRead.model_validate(c) for c in companies],
            total=count,
        )

    async def get(self, company_id: uuid.UUID) -> Company | None:
        stmt = (
            select(Company)
            .options(selectinload(Company.signals))
            .where(Company.id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def set_watched(self, company_id: uuid.UUID, watched: bool) -> None:
        company = await self.db.get(Company, company_id)
        if company:
            company.is_watched = watched
            await self.db.commit()

    async def get_signals(self, company_id: uuid.UUID) -> list[CompanySignalRead]:
        stmt = (
            select(CompanySignal)
            .where(CompanySignal.company_id == company_id)
            .order_by(CompanySignal.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return [CompanySignalRead.model_validate(s) for s in result.scalars().all()]
