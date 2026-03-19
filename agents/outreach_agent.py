"""
Recruiter Outreach Agent

Generates a personalised recruiter outreach message using the LLM
content generator. Falls back to a structured template when LLM is
unavailable.
"""
from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent


class OutreachAgent(BaseAgent):
    """Generate a recruiter outreach message for a specific job."""

    name = "outreach"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from engines.content.generator import ContentGenerator

        profile = input_data.get("profile", {})
        matching = input_data.get("matching", {})

        # Build a lightweight job stub for the generator
        job = _JobStub(
            title=input_data.get("title", "the role"),
            company_name=input_data.get("company_name", "your company"),
        )

        # Build a lightweight profile stub
        profile_stub = _ProfileStub(
            full_name=profile.get("full_name", ""),
            experience_years=profile.get("experience_years", 0),
            skills=profile.get("skills", []),
        )

        generator = ContentGenerator()
        result = await generator.generate(
            content_type="recruiter_outreach",
            job=job,
            tone="professional",
            profile=profile_stub,
        )

        body = result.get("body", "")
        subject = result.get("subject", f"Re: {job.title} opportunity")
        model_used = result.get("model_used", "fallback")

        return {
            "message_text": body.strip() if body else _fallback_message(job, profile_stub),
            "subject": subject,
            "model_used": model_used,
        }


def _fallback_message(job: Any, profile: Any) -> str:
    return (
        f"Hi,\n\n"
        f"I came across the {job.title} role at {job.company_name} and I'm very interested. "
        f"With {profile.experience_years} years of experience in the field, I believe I'd be "
        f"a strong contributor to your team.\n\n"
        f"Would you be open to a quick call to discuss the opportunity?\n\n"
        f"Best regards,\n{profile.full_name}"
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
