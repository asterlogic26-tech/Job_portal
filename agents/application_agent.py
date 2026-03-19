"""
Application Agent

Prepares a complete application workflow: step-by-step action plan,
anticipated form field data, and a readiness status.
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent


_STANDARD_STEPS = [
    "Tailor your resume to highlight matched skills",
    "Write a customised cover letter using the generated draft",
    "Research the company's recent news, products, and culture",
    "Apply via the job URL — complete all required form fields",
    "Connect with a recruiter or employee on LinkedIn",
    "Set a follow-up reminder for 7 days after applying",
]

_HIGH_MATCH_EXTRA_STEPS = [
    "Reach out to a network connection at the company for a referral",
    "Prepare 2-3 STAR stories aligned with the key requirements",
]

_LOW_MATCH_STEPS = [
    "Consider addressing skill gaps in your cover letter proactively",
    "Research courses or projects to quickly demonstrate missing skills",
]


class ApplicationAgent(BaseAgent):
    """Prepare the application workflow and pre-fill form data."""

    name = "application"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        matching = input_data.get("matching", {})
        profile = input_data.get("profile", {})
        job_analysis = input_data.get("job_analysis", {})

        match_score = float(matching.get("match_score", 0))
        apply_url = input_data.get("apply_url") or input_data.get("url", "")

        # Build step list based on match quality
        steps: List[str] = list(_STANDARD_STEPS)
        if match_score >= 70:
            steps[3:3] = _HIGH_MATCH_EXTRA_STEPS
        elif match_score < 40:
            steps.extend(_LOW_MATCH_STEPS)

        # Pre-fill anticipated form data from profile
        skills_str = ", ".join(
            s.get("name", s) if isinstance(s, dict) else s
            for s in profile.get("skills", [])[:10]
        )
        form_data: Dict[str, Any] = {
            "full_name": profile.get("full_name", ""),
            "email": profile.get("email", ""),
            "linkedin_url": profile.get("linkedin_url", ""),
            "github_url": profile.get("github_url", ""),
            "current_title": profile.get("current_title", ""),
            "years_of_experience": profile.get("experience_years", 0),
            "skills_summary": skills_str,
            "resume_url": profile.get("resume_url", ""),
            "target_salary": _format_salary(
                profile.get("target_salary_min"),
                profile.get("target_salary_max"),
            ),
            "apply_url": apply_url,
        }

        # Readiness status
        missing = matching.get("missing_skills", [])
        if match_score >= 50 and len(missing) <= 3:
            status = "ready"
        elif match_score >= 30:
            status = "needs_prep"
        else:
            status = "consider_skipping"

        return {
            "application_steps": steps,
            "form_data": form_data,
            "status": status,
        }


def _format_salary(min_sal: int | None, max_sal: int | None) -> str:
    if min_sal and max_sal:
        return f"${min_sal:,} – ${max_sal:,}"
    if min_sal:
        return f"${min_sal:,}+"
    if max_sal:
        return f"Up to ${max_sal:,}"
    return "Negotiable"
