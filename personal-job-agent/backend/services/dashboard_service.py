import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from backend.models.job import Job
from backend.models.job_match import JobMatch
from backend.models.application import Application
from backend.models.company import Company
from backend.models.manual_task import ManualTask
from backend.models.notification import Notification
from backend.models.content import Content
from backend.models.user_profile import UserProfile
from backend.schemas.dashboard import DashboardSummary, ApplicationsByStatus
import datetime


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, user_id: uuid.UUID) -> DashboardSummary:
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Job stats
        total_jobs = (await self.db.execute(
            select(func.count(Job.id)).where(Job.is_hidden == False, Job.is_duplicate == False)
        )).scalar_one()

        new_today = (await self.db.execute(
            select(func.count(Job.id)).where(Job.created_at >= today)
        )).scalar_one()

        high_match = (await self.db.execute(
            select(func.count(JobMatch.id)).where(JobMatch.total_score >= 0.75)
        )).scalar_one()

        saved_jobs = (await self.db.execute(
            select(func.count(Job.id)).where(Job.is_saved == True)
        )).scalar_one()

        # Application pipeline
        total_apps = (await self.db.execute(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )).scalar_one()

        # By status
        status_rows = (await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )).all()
        applications_by_status = [
            ApplicationsByStatus(status=row[0], count=row[1]) for row in status_rows
        ]

        active_statuses = {"applied", "phone_screen", "technical_interview", "onsite_interview", "offer"}
        active_apps = sum(
            r.count for r in applications_by_status if r.status in active_statuses
        )

        interviews = sum(
            r.count for r in applications_by_status
            if r.status in {"phone_screen", "technical_interview", "onsite_interview"}
        )

        # Companies
        watched = (await self.db.execute(
            select(func.count(Company.id)).where(Company.is_watched == True)
        )).scalar_one()

        hiring = (await self.db.execute(
            select(func.count(Company.id)).where(Company.hiring_score >= 0.5)
        )).scalar_one()

        # Tasks
        pending_tasks = (await self.db.execute(
            select(func.count(ManualTask.id))
            .where(ManualTask.user_id == user_id, ManualTask.status == "pending")
        )).scalar_one()

        unread_notifs = (await self.db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read == False)
        )).scalar_one()

        # Content
        pending_drafts = (await self.db.execute(
            select(func.count(Content.id))
            .where(Content.user_id == user_id, Content.status == "draft")
        )).scalar_one()

        # Profile health
        profile = await self.db.get(UserProfile, user_id)
        health_score = profile.health_score if profile else 0

        return DashboardSummary(
            total_jobs_discovered=total_jobs,
            new_jobs_today=new_today,
            high_match_jobs=high_match,
            saved_jobs=saved_jobs,
            total_applications=total_apps,
            applications_by_status=applications_by_status,
            active_applications=active_apps,
            interviews_scheduled=interviews,
            watched_companies=watched,
            companies_hiring=hiring,
            pending_manual_tasks=pending_tasks,
            unread_notifications=unread_notifs,
            pending_content_drafts=pending_drafts,
            profile_health_score=health_score,
        )
