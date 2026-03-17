from pydantic import BaseModel


class ApplicationsByStatus(BaseModel):
    status: str
    count: int


class DashboardSummary(BaseModel):
    # Job stats
    total_jobs_discovered: int
    new_jobs_today: int
    high_match_jobs: int
    saved_jobs: int

    # Application pipeline
    total_applications: int
    applications_by_status: list[ApplicationsByStatus]
    active_applications: int
    interviews_scheduled: int

    # Companies
    watched_companies: int
    companies_hiring: int

    # Tasks
    pending_manual_tasks: int
    unread_notifications: int

    # Content
    pending_content_drafts: int

    # Health
    profile_health_score: int
