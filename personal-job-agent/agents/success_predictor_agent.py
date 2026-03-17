"""
Success Predictor Agent

Estimates the probability of getting an interview based on the
match score, skill coverage, experience gap, network proximity,
and company hiring momentum.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from agents.base import BaseAgent


def _label(prob: float) -> str:
    if prob >= 70:
        return "High"
    if prob >= 40:
        return "Moderate"
    return "Low"


class SuccessPredictorAgent(BaseAgent):
    """Predict interview probability using the rule-based predictor engine."""

    name = "success_predictor"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from engines.predictor.predictor import predict_interview_probability

        matching = input_data.get("matching", {})
        profile = input_data.get("profile", {})
        job_analysis = input_data.get("job_analysis", {})

        match_score = float(matching.get("match_score", 0))
        skill_coverage_pct = float(matching.get("skill_coverage_pct", 0))
        experience_years = int(profile.get("experience_years", 0))
        network_count = int(input_data.get("network_connections_at_company", 0))
        company_hiring_score = float(input_data.get("company_hiring_score", 50))

        # Infer minimum required years from experience level
        _year_map = {
            "intern": 0, "junior": 0, "mid": 2, "senior": 5,
            "staff": 7, "lead": 5, "director": 10, "principal": 10,
        }
        level = (
            job_analysis.get("experience_level")
            or input_data.get("seniority_level", "mid")
            or "mid"
        ).lower()
        required_years_min = _year_map.get(level, 2)

        # Calculate posting age in days
        posting_age_days = 0
        raw_posted_at = input_data.get("posted_at")
        if raw_posted_at:
            try:
                if isinstance(raw_posted_at, str):
                    raw_posted_at = datetime.fromisoformat(raw_posted_at)
                if raw_posted_at.tzinfo is None:
                    raw_posted_at = raw_posted_at.replace(tzinfo=timezone.utc)
                posting_age_days = max(0, (datetime.now(timezone.utc) - raw_posted_at).days)
            except Exception:
                posting_age_days = 0

        result = predict_interview_probability(
            match_score=match_score,
            skill_coverage_pct=skill_coverage_pct,
            experience_years=experience_years,
            required_years_min=required_years_min,
            network_connections_at_company=network_count,
            posting_age_days=posting_age_days,
            company_hiring_score=company_hiring_score,
        )

        prob = result["interview_probability"]
        return {
            "success_score": prob,
            "probability_label": _label(prob),
            "confidence_score": result.get("confidence_score", 0),
            "key_factors": result.get("key_factors", []),
            "breakdown": result.get("breakdown", {}),
        }
