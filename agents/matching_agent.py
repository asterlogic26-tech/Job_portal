"""
Matching Agent

Compares a job against the user profile using the existing scoring
engine and returns a comprehensive match result.
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent
from agents._llm import normalize_skills


class MatchingAgent(BaseAgent):
    """Score job vs. user profile using the matching engine."""

    name = "matching"

    def validate(self, input_data: Dict[str, Any]) -> bool:
        return bool(input_data.get("profile"))

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from engines.matching.matcher import compute_match_score

        profile = input_data.get("profile", {})

        # Prefer skills extracted by the Job Analysis Agent (normalized list)
        job_analysis = input_data.get("job_analysis", {})
        raw_skills = (
            job_analysis.get("required_skills")
            or normalize_skills(input_data.get("required_skills", []))
        )

        # Build dicts in the format expected by compute_match_score
        job_dict = {
            "skills_required": [{"name": s} for s in raw_skills],
            "seniority_level": (
                job_analysis.get("experience_level")
                or input_data.get("seniority_level", "unknown")
            ),
            "salary_min": input_data.get("salary_min"),
            "salary_max": input_data.get("salary_max"),
            "posted_at": input_data.get("posted_at"),
        }
        profile_dict = {
            "skills": profile.get("skills", []),
            "experience_years": profile.get("experience_years", 0),
            "target_salary_min": profile.get("target_salary_min"),
            "target_salary_max": profile.get("target_salary_max"),
        }
        company_hiring_score = float(input_data.get("company_hiring_score", 0))

        result = compute_match_score(job_dict, profile_dict, company_hiring_score)

        # Extract the flat matched / missing skill lists for downstream agents
        breakdown = result.get("scoring_breakdown", {})
        skill_breakdown = breakdown.get("skill_overlap", {})
        matched: List[str] = skill_breakdown.get("matched_skills", [])
        missing: List[str] = skill_breakdown.get("missing_skills", [])

        return {
            "match_score": result["match_score"],
            "matched_skills": matched,
            "missing_skills": missing,
            # Extra context forwarded to downstream agents
            "skill_coverage_pct": result.get("skill_coverage_pct", 0),
            "seniority_fit_score": result.get("seniority_fit_score", 0),
            "salary_alignment_score": result.get("salary_alignment_score", 0),
            "risk_factors": result.get("risk_factors", []),
            "strength_factors": result.get("strength_factors", []),
        }
