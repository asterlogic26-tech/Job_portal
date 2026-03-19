import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def predict_interview_probability(
    match_score: float,
    skill_coverage_pct: float,
    experience_years: int,
    required_years_min: int,
    network_connections_at_company: int = 0,
    posting_age_days: int = 0,
    company_hiring_score: float = 50.0,
) -> Dict:
    """
    Rule-based interview probability predictor.
    Returns probability 0-100 with confidence and key factors.
    """
    # Base probability from match score
    base = match_score * 0.35

    # Skill coverage contribution
    skill_contrib = (skill_coverage_pct / 100) * 25

    # Experience alignment
    exp_gap = max(0, required_years_min - experience_years)
    exp_penalty = min(exp_gap * 3, 20)

    # Network bonus
    network_bonus = min(network_connections_at_company * 5, 15)

    # Posting freshness
    recency_bonus = max(0, 10 - posting_age_days * 0.5)

    # Company hiring momentum
    radar_bonus = (company_hiring_score / 100) * 10

    raw_prob = base + skill_contrib - exp_penalty + network_bonus + recency_bonus + radar_bonus

    # Clamp to 0-95 (never predict 100%)
    probability = round(max(5.0, min(95.0, raw_prob)), 1)

    # Confidence based on data completeness
    data_points = sum([
        1 if match_score > 0 else 0,
        1 if skill_coverage_pct > 0 else 0,
        1 if experience_years > 0 else 0,
        1 if required_years_min > 0 else 0,
    ])
    confidence = round((data_points / 4) * 100, 1)

    # Key factors
    factors = []
    if skill_coverage_pct >= 70:
        factors.append(f"High skill match ({skill_coverage_pct:.0f}%)")
    if network_connections_at_company > 0:
        factors.append(f"{network_connections_at_company} network connection(s) at company")
    if exp_gap > 2:
        factors.append(f"Experience gap: {exp_gap} years below requirement")
    if posting_age_days > 30:
        factors.append("Posting is older — may have many applicants")
    if company_hiring_score > 70:
        factors.append("Company is actively hiring (high radar score)")

    return {
        "interview_probability": probability,
        "confidence_score": confidence,
        "key_factors": factors,
        "breakdown": {
            "base_from_match": round(base, 1),
            "skill_contribution": round(skill_contrib, 1),
            "experience_penalty": -round(exp_penalty, 1),
            "network_bonus": round(network_bonus, 1),
            "recency_bonus": round(recency_bonus, 1),
            "radar_bonus": round(radar_bonus, 1),
        },
    }
