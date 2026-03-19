import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile
from backend.models.user_profile import UserProfile
from backend.schemas.profile import ProfileRead, ProfileUpdate, ProfileHealthRead
from backend.core.config import settings


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: uuid.UUID) -> ProfileRead:
        profile = await self.db.get(UserProfile, user_id)
        if not profile:
            profile = UserProfile(id=user_id, full_name="Job Seeker")
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        return ProfileRead.model_validate(profile)

    async def update(self, user_id: uuid.UUID, payload: ProfileUpdate) -> ProfileRead:
        profile = await self.db.get(UserProfile, user_id)
        if not profile:
            profile = UserProfile(id=user_id, full_name="Job Seeker")
            self.db.add(profile)

        for field, val in payload.model_dump(exclude_none=True).items():
            if field == "skills" and val is not None:
                val = [s.model_dump() if hasattr(s, 'model_dump') else s for s in val]
            setattr(profile, field, val)

        await self.db.commit()
        await self.db.refresh(profile)
        return ProfileRead.model_validate(profile)

    async def get_health(self, user_id: uuid.UUID) -> ProfileHealthRead:
        from engines.profile.health_checker import ProfileHealthChecker

        profile = await self.db.get(UserProfile, user_id)
        if not profile:
            return ProfileHealthRead(score=0, grade="F", missing_fields=["profile"], suggestions=[])

        checker = ProfileHealthChecker()
        result = checker.check(profile.__dict__)

        # Persist score
        profile.health_score = result["score"]
        await self.db.commit()

        return ProfileHealthRead(
            score=result["score"],
            grade=result["grade"],
            missing_fields=result.get("missing_fields", []),
            suggestions=result.get("suggestions", []),
        )

    async def upload_resume(self, user_id: uuid.UUID, file: UploadFile) -> str:
        if not settings.enable_minio:
            return "minio-disabled"

        from integrations.storage.document_store import DocumentStore
        store = DocumentStore()
        content = await file.read()
        key = f"resumes/{user_id}/{file.filename}"
        url = await store.upload(bucket=settings.minio_bucket_resumes, key=key, data=content)

        profile = await self.db.get(UserProfile, user_id)
        if profile:
            profile.resume_url = url
            await self.db.commit()

        return url

    async def refresh_embedding(self, user_id: uuid.UUID) -> None:
        from engines.embedding.embedder import embed_text
        from engines.embedding.vector_store import VectorStore

        profile = await self.db.get(UserProfile, user_id)
        if not profile:
            return

        skill_names = [s["name"] if isinstance(s, dict) else s for s in (profile.skills or [])]
        text = f"{profile.current_title} {' '.join(skill_names)} {profile.bio}"
        embedding = embed_text(text)

        store = VectorStore()
        point_id = str(user_id)
        await store.upsert("profiles", point_id, embedding, {"user_id": str(user_id)})

        profile.profile_embedding_id = point_id
        await self.db.commit()
