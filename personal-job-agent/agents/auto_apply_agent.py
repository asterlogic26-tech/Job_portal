"""
Auto-Apply Agent

Attempts to automatically submit the job application after the pipeline
has generated a tailored resume summary and cover letter.

Output keys:
    applied            bool    — True if submission went through
    apply_method       str     — playwright | blocked | error
    ats_detected       str|None
    fields_filled      list[str]
    blocked            bool    — True if human intervention is needed
    blocked_reason     str|None
    direct_apply_url   str     — URL to apply manually (always populated)
    confidence         int     — 0-100 confidence application was received
    cover_letter       str     — the cover letter text used
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent


class AutoApplyAgent(BaseAgent):
    """Attempt automated application submission for a job."""

    name = "auto_apply"

    def validate(self, input_data: Dict[str, Any]) -> bool:
        # Require at least an apply URL or job URL
        return bool(
            input_data.get("apply_url")
            or input_data.get("url")
        )

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from engines.apply.auto_apply_engine import run_auto_apply
        from engines.content.generator import ContentGenerator

        profile = input_data.get("profile", {})
        resume = input_data.get("resume", {})

        apply_url = input_data.get("apply_url") or input_data.get("url", "")

        # ── Step 1: Generate cover letter ─────────────────────────────────────
        cover_letter_text = await self._generate_cover_letter(input_data, profile)

        # ── Step 2: Prepare profile dict for form filler ─────────────────────
        profile_for_fill = {
            "full_name": profile.get("full_name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "linkedin_url": profile.get("linkedin_url", ""),
            "resume_url": profile.get("resume_url"),
        }

        # ── Step 3: Attempt auto-apply ────────────────────────────────────────
        job_dict = {
            "title": input_data.get("title", ""),
            "company_name": input_data.get("company_name", ""),
            "description": input_data.get("description", ""),
        }

        result = await run_auto_apply(
            apply_url=apply_url,
            profile=profile_for_fill,
            job=job_dict,
            cover_letter=cover_letter_text,
        )
        result["cover_letter"] = cover_letter_text
        result["direct_apply_url"] = apply_url
        return result

    async def _generate_cover_letter(
        self, input_data: Dict[str, Any], profile: Dict[str, Any]
    ) -> str:
        """Generate a tailored cover letter using the LLM content generator."""
        from engines.content.generator import ContentGenerator

        try:
            job = _JobStub(
                title=input_data.get("title", "the role"),
                company_name=input_data.get("company_name", "the company"),
            )
            profile_stub = _ProfileStub(
                full_name=profile.get("full_name", ""),
                experience_years=profile.get("experience_years", 0),
                skills=profile.get("skills", []),
            )

            generator = ContentGenerator()
            result = await generator.generate(
                content_type="cover_letter",
                job=job,
                profile=profile_stub,
                tone="professional",
            )
            return result.get("body", "").strip()
        except Exception as exc:
            self.logger.warning("Cover letter generation failed: %s", exc)
            return _fallback_cover_letter(
                input_data.get("title", "the role"),
                input_data.get("company_name", "your company"),
                profile.get("full_name", ""),
            )


def _fallback_cover_letter(job_title: str, company: str, name: str) -> str:
    return (
        f"Dear Hiring Team,\n\n"
        f"I am excited to apply for the {job_title} role at {company}. "
        f"With my background and skills, I am confident I would make a strong "
        f"contribution to your team.\n\n"
        f"I would welcome the opportunity to discuss how my experience aligns "
        f"with your needs.\n\n"
        f"Best regards,\n{name}"
    )


class _JobStub:
    def __init__(self, title: str, company_name: str):
        self.title = title
        self.company_name = company_name


class _ProfileStub:
    def __init__(self, full_name: str, experience_years: int, skills: list):
        self.full_name = full_name
        self.experience_years = experience_years
        self.skills = skills
