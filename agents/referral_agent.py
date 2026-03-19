"""
Referral Agent

Generates a referral request message targeting the strongest
network connection at the target company.
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent


class ReferralAgent(BaseAgent):
    """Generate a referral request message for a network connection."""

    name = "referral"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from engines.content.generator import ContentGenerator

        profile = input_data.get("profile", {})
        network_connections: List[Dict] = input_data.get("network_connections", [])

        job_title = input_data.get("title", "the role")
        company_name = input_data.get("company_name", "the company")
        sender_name = profile.get("full_name", "Candidate")

        # Find the strongest connection at this company
        target = _best_connection(network_connections, company_name)

        if target:
            recipient_name = target.get("full_name", "")
            relationship = (
                "close professional connection"
                if float(target.get("relationship_strength", 0)) >= 0.7
                else "professional contact"
            )
        else:
            recipient_name = "colleague"
            relationship = "professional contact"

        job = _JobStub(title=job_title, company_name=company_name)
        profile_stub = _ProfileStub(
            full_name=sender_name,
            experience_years=profile.get("experience_years", 0),
            skills=profile.get("skills", []),
        )

        generator = ContentGenerator()
        result = await generator.generate(
            content_type="referral_request",
            job=job,
            target_person=recipient_name,
            target_company=company_name,
            profile=profile_stub,
        )

        body = result.get("body", "")
        return {
            "referral_message": body.strip() if body else _fallback_referral(
                sender_name, recipient_name, job_title, company_name
            ),
            "target_contact": recipient_name or None,
            "model_used": result.get("model_used", "fallback"),
        }


def _best_connection(connections: List[Dict], company: str) -> Dict | None:
    """Return the strongest network connection at the target company."""
    at_company = [
        c for c in connections
        if company.lower() in (c.get("current_company") or "").lower()
    ]
    if not at_company:
        return None
    return max(at_company, key=lambda c: float(c.get("relationship_strength", 0)))


def _fallback_referral(sender: str, recipient: str, job_title: str, company: str) -> str:
    greet = f"Hi {recipient}," if recipient else "Hi,"
    return (
        f"{greet}\n\n"
        f"I hope this message finds you well. I wanted to reach out because I'm very interested "
        f"in the {job_title} role at {company} and thought of you as someone who might be able "
        f"to offer a referral or an introduction.\n\n"
        f"I'd really value any support you can offer. Happy to share my resume and chat briefly "
        f"if that's helpful.\n\n"
        f"Thanks so much,\n{sender}"
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
