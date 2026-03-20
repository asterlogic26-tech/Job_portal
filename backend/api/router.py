from fastapi import APIRouter
from backend.api.v1 import (
    auth,
    jobs,
    applications,
    companies,
    content,
    notifications,
    manual_tasks,
    profile,
    dashboard,
    resume,
    agents,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(manual_tasks.router, prefix="/manual-tasks", tags=["manual-tasks"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
