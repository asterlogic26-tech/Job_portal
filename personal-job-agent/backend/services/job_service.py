import uuid
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from backend.models.job import Job
from backend.models.job_match import JobMatch
from backend.schemas.job import JobListResponse, JobFilter, JobRead, JobMatchRead


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_jobs(self, user_id: uuid.UUID, f: JobFilter) -> JobListResponse:
        stmt = (
            select(Job)
            .outerjoin(JobMatch, Job.id == JobMatch.job_id)
            .options(selectinload(Job.match))
            .where(Job.is_hidden == False, Job.is_duplicate == False)
        )

        if f.q:
            search = f"%{f.q}%"
            stmt = stmt.where(
                or_(
                    Job.title.ilike(search),
                    Job.company_name.ilike(search),
                    Job.location.ilike(search),
                )
            )
        if f.remote_only:
            stmt = stmt.where(Job.remote_policy.in_(["remote", "flexible"]))
        if f.min_score is not None:
            stmt = stmt.where(JobMatch.total_score >= f.min_score)
        if f.seniority:
            stmt = stmt.where(Job.seniority_level == f.seniority)
        if f.source:
            stmt = stmt.where(Job.source == f.source)
        if f.saved_only:
            stmt = stmt.where(Job.is_saved == True)

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Paginate + order by match score desc, then created_at desc
        stmt = (
            stmt
            .order_by(desc(JobMatch.total_score), desc(Job.created_at))
            .offset((f.page - 1) * f.page_size)
            .limit(f.page_size)
        )

        result = await self.db.execute(stmt)
        jobs = result.scalars().all()

        return JobListResponse(
            items=[JobRead.model_validate(j) for j in jobs],
            total=total,
            page=f.page,
            page_size=f.page_size,
        )

    async def get_job(self, job_id: uuid.UUID) -> Job | None:
        stmt = (
            select(Job)
            .options(selectinload(Job.match))
            .where(Job.id == job_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def set_hidden(self, job_id: uuid.UUID, hidden: bool) -> None:
        job = await self.db.get(Job, job_id)
        if job:
            job.is_hidden = hidden
            await self.db.commit()

    async def set_saved(self, job_id: uuid.UUID, saved: bool) -> None:
        job = await self.db.get(Job, job_id)
        if job:
            job.is_saved = saved
            await self.db.commit()
