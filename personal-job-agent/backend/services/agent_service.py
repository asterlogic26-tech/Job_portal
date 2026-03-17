"""
AgentService — bridges the async FastAPI layer with the Agent Orchestrator.

Responsibilities:
  1. Load job + profile data from the DB and build the pipeline context.
  2. Invoke the AgentOrchestrator.
  3. Persist AgentLog records for every agent execution.
  4. Optionally persist pipeline outputs back to domain tables
     (JobMatch, Content, etc.).
"""
from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.agent_log import AgentLog
from backend.models.job import Job
from backend.models.company import Company
from backend.models.company_signal import CompanySignal
from backend.models.network_connection import NetworkConnection
from backend.models.user_profile import UserProfile
from backend.schemas.agent import AgentLogRead, AgentLogListResponse


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Context builder ────────────────────────────────────────────────────

    async def build_context(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Load all data needed to run the agent pipeline for a job."""

        # Load job
        job = await self.db.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Load profile
        profile_row = await self.db.get(UserProfile, user_id)

        # Load company (optional)
        company: Optional[Company] = None
        if job.company_id:
            company = await self.db.get(Company, job.company_id)

        # Load company signals
        company_signals: List[Dict] = []
        if company:
            sig_stmt = (
                select(CompanySignal)
                .where(CompanySignal.company_id == company.id)
                .order_by(CompanySignal.signal_date.desc())
                .limit(10)
            )
            sig_result = await self.db.execute(sig_stmt)
            company_signals = [
                {
                    "signal_type": s.signal_type,
                    "title": s.title,
                    "summary": s.summary,
                    "amount_usd": s.amount_usd,
                }
                for s in sig_result.scalars().all()
            ]

        # Count network connections at this company
        net_stmt = select(func.count()).where(
            NetworkConnection.user_id == user_id,
            func.lower(NetworkConnection.current_company).contains(
                job.company_name.lower()
            ),
        )
        network_count = (await self.db.execute(net_stmt)).scalar_one()

        # Load network connection details for referral agent
        net_detail_stmt = (
            select(NetworkConnection)
            .where(
                NetworkConnection.user_id == user_id,
                func.lower(NetworkConnection.current_company).contains(
                    job.company_name.lower()
                ),
            )
            .limit(5)
        )
        net_result = await self.db.execute(net_detail_stmt)
        network_connections = [
            {
                "full_name": c.full_name,
                "current_company": c.current_company,
                "title": c.title,
                "linkedin_url": c.linkedin_url,
                "relationship_strength": c.relationship_strength,
                "can_refer": c.can_refer,
            }
            for c in net_result.scalars().all()
        ]

        profile_dict: Dict[str, Any] = {}
        if profile_row:
            profile_dict = {
                "full_name": profile_row.full_name,
                "current_title": profile_row.current_title,
                "skills": profile_row.skills or [],
                "experience_years": profile_row.experience_years,
                "location": profile_row.location,
                "remote_preference": profile_row.remote_preference,
                "target_salary_min": profile_row.target_salary_min,
                "target_salary_max": profile_row.target_salary_max,
                "linkedin_url": profile_row.linkedin_url,
                "github_url": profile_row.github_url,
                "resume_url": profile_row.resume_url,
                "bio": profile_row.bio,
                "target_titles": profile_row.target_titles or [],
            }

        context: Dict[str, Any] = {
            "job_id": str(job_id),
            "title": job.title,
            "company_name": job.company_name,
            "company_id": str(job.company_id) if job.company_id else None,
            "description": job.description,
            "seniority_level": job.seniority_level,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "url": job.url,
            "apply_url": job.apply_url,
            "posted_at": job.posted_at,
            "source": job.source,
            "profile": profile_dict,
            "company_hiring_score": company.hiring_score if company else 0.0,
            "company_signals": company_signals,
            "network_connections_at_company": network_count,
            "network_connections": network_connections,
        }

        if additional_context:
            context.update(additional_context)

        return context

    # ── Pipeline execution ─────────────────────────────────────────────────

    async def run_pipeline(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build context, run the orchestrator, persist logs, return results."""
        from agents.orchestrator import AgentOrchestrator

        context = await self.build_context(job_id, user_id, additional_context)
        orchestrator = AgentOrchestrator()
        results = await orchestrator.run_pipeline(context)

        # Persist agent logs
        saved = await self._save_logs(
            agent_logs=results["agent_logs"],
            job_id=job_id,
            user_id=user_id,
        )
        results["agent_logs_saved"] = saved
        return results

    async def run_single_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        job_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Run one named agent and persist its log."""
        from agents.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        output = await orchestrator.run_single(agent_name, input_data)

        # Persist single log entry
        log = AgentLog(
            agent_name=agent_name,
            job_id=job_id,
            user_id=user_id,
            input_data=input_data,
            output_data=output,
            error_message=output.get("error"),
            duration_ms=0.0,
            success="error" not in output,
        )
        self.db.add(log)
        await self.db.commit()

        return output

    # ── Log persistence ────────────────────────────────────────────────────

    async def _save_logs(
        self,
        agent_logs: List[Dict[str, Any]],
        job_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
    ) -> int:
        """Write all agent log entries to the DB in one flush."""
        entries: List[AgentLog] = []
        for entry in agent_logs:
            run_id_raw = entry.get("pipeline_run_id")
            try:
                run_id = uuid.UUID(str(run_id_raw)) if run_id_raw else None
            except ValueError:
                run_id = None

            log = AgentLog(
                agent_name=entry.get("agent_name", "unknown"),
                version=entry.get("version", "1.0.0"),
                pipeline_run_id=run_id,
                job_id=job_id,
                user_id=user_id,
                input_data=_truncate(entry.get("input", {})),
                output_data=entry.get("output", {}),
                error_message=entry.get("error"),
                duration_ms=entry.get("duration_ms", 0.0),
                success=entry.get("success", False),
            )
            entries.append(log)

        for log in entries:
            self.db.add(log)
        await self.db.commit()
        return len(entries)

    # ── Log queries ────────────────────────────────────────────────────────

    async def list_logs(
        self,
        job_id: Optional[uuid.UUID] = None,
        agent_name: Optional[str] = None,
        pipeline_run_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 30,
    ) -> AgentLogListResponse:
        stmt = select(AgentLog)
        if job_id:
            stmt = stmt.where(AgentLog.job_id == job_id)
        if agent_name:
            stmt = stmt.where(AgentLog.agent_name == agent_name)
        if pipeline_run_id:
            stmt = stmt.where(AgentLog.pipeline_run_id == pipeline_run_id)

        total = (
            await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        stmt = (
            stmt.order_by(AgentLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return AgentLogListResponse(
            items=[AgentLogRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )


def _truncate(data: Any, max_chars: int = 4000) -> Any:
    """Truncate large input dicts so they fit comfortably in JSONB."""
    import json
    try:
        raw = json.dumps(data)
        if len(raw) <= max_chars:
            return data
        # Return a trimmed representation
        return {"_truncated": True, "preview": raw[:max_chars]}
    except Exception:
        return {}
