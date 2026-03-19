import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.content import Content
from backend.models.user_profile import UserProfile
from backend.schemas.content import ContentRead, ContentGenerate, ContentUpdate, ContentListResponse
from backend.core.config import settings


class ContentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        user_id: uuid.UUID,
        content_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ContentListResponse:
        stmt = select(Content).where(Content.user_id == user_id)
        if content_type:
            stmt = stmt.where(Content.content_type == content_type)
        if status:
            stmt = stmt.where(Content.status == status)

        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
        stmt = stmt.order_by(Content.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return ContentListResponse(
            items=[ContentRead.model_validate(c) for c in items],
            total=total,
        )

    async def get(self, content_id: uuid.UUID) -> Content | None:
        return await self.db.get(Content, content_id)

    async def generate(self, user_id: uuid.UUID, payload: ContentGenerate) -> ContentRead:
        from engines.content.generator import ContentGenerator
        from backend.services.job_service import JobService
        from backend.services.profile_service import ProfileService

        profile_svc = ProfileService(self.db)
        profile = await profile_svc.get_or_create(user_id)

        job_data = {}
        if payload.job_id:
            job_svc = JobService(self.db)
            job = await job_svc.get_job(payload.job_id)
            if job:
                job_data = {
                    "title": job.title,
                    "company_name": job.company_name,
                    "description": getattr(job, "description", ""),
                    "required_skills": job.required_skills,
                }

        generator = ContentGenerator()
        result = await generator.generate(
            content_type=payload.content_type,
            profile_data={
                "full_name": profile.full_name,
                "current_title": profile.current_title,
                "skills": profile.skills,
                "experience_years": profile.experience_years,
                "bio": profile.bio,
            },
            job_data=job_data,
            extra_context=payload.extra_context,
        )

        content = Content(
            user_id=user_id,
            content_type=payload.content_type,
            status="draft",
            title=result.get("title", f"{payload.content_type} draft"),
            body=result.get("body", ""),
            subject=result.get("subject", ""),
            job_id=payload.job_id,
            company_id=payload.company_id,
            application_id=payload.application_id,
            model_used=result.get("model_used", ""),
            generation_metadata=result.get("metadata", {}),
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        return ContentRead.model_validate(content)

    async def update(self, content_id: uuid.UUID, payload: ContentUpdate) -> Content | None:
        content = await self.db.get(Content, content_id)
        if not content:
            return None
        for field, val in payload.model_dump(exclude_none=True).items():
            setattr(content, field, val)
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def approve(self, content_id: uuid.UUID) -> Content | None:
        content = await self.db.get(Content, content_id)
        if not content:
            return None
        content.is_approved = True
        content.status = "approved"
        content.approved_at = datetime.datetime.utcnow().isoformat()
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def delete(self, content_id: uuid.UUID) -> None:
        content = await self.db.get(Content, content_id)
        if content:
            await self.db.delete(content)
            await self.db.commit()
