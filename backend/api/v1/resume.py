import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.common import MessageResponse

router = APIRouter()


class ResumeCustomizeRequest(BaseModel):
    job_id: uuid.UUID


class ResumeCustomizeResponse(BaseModel):
    ats_score: float
    keyword_gaps: list[str]
    suggested_summary: str
    tailoring_tips: list[str]


@router.post("/customize", response_model=ResumeCustomizeResponse)
async def customize_resume(
    payload: ResumeCustomizeRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    from backend.services.profile_service import ProfileService
    from backend.services.job_service import JobService
    from engines.resume.customizer import ResumeCustomizer

    profile_svc = ProfileService(db)
    job_svc = JobService(db)

    profile = await profile_svc.get_or_create(user_id)
    job = await job_svc.get_job(payload.job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    customizer = ResumeCustomizer()
    result = await customizer.customize(
        profile_data={
            "skills": [s.model_dump() if hasattr(s, 'model_dump') else s for s in profile.skills],
            "experience_years": profile.experience_years,
            "bio": profile.bio,
            "current_title": profile.current_title,
        },
        job_data={
            "title": job.title,
            "description": job.description if hasattr(job, 'description') else "",
            "required_skills": job.required_skills,
            "company_name": job.company_name,
        },
    )

    return ResumeCustomizeResponse(
        ats_score=result.get("ats_score", 0.0),
        keyword_gaps=result.get("keyword_gaps", []),
        suggested_summary=result.get("suggested_summary", ""),
        tailoring_tips=result.get("tailoring_tips", []),
    )
