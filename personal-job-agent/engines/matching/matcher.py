import logging
from typing import Optional

import yaml
import os

from engines.matching.skill_scorer import compute_skill_score
from engines.matching.seniority_scorer import compute_seniority_score
from engines.matching.salary_scorer import compute_salary_score
from engines.matching.recency_scorer import compute_recency_score

logger = logging.getLogger(__name__)

# Default weights
DEFAULT_WEIGHTS = {
    "skill_overlap": 0.30,
    "seniority_fit": 0.20,
    "culture_fit": 0.15,
    "company_growth_signal": 0.15,
    "salary_alignment": 0.10,
    "recency_score": 0.10,
}


def load_weights() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/scoring_weights.yml")
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
            return data.get("matching_weights", DEFAULT_WEIGHTS)
    except Exception:
        return DEFAULT_WEIGHTS


def compute_match_score(job: dict, profile: dict, company_hiring_score: float = 0.0) -> dict:
    """
    Compute a full match between a job and user profile.

    Args:
        job: dict with job fields (skills_required, seniority_level, salary_min/max, etc.)
        profile: dict with profile fields (skills, experience_years, target_salary_min/max, etc.)
        company_hiring_score: float 0-100 from company radar

    Returns:
        dict with match_score, breakdown, risk/strength factors
    """
    weights = load_weights()

    # 1. Skill overlap
    job_skills = [s.get("name", "").lower() for s in (job.get("skills_required") or [])]
    profile_skills = [s.get("name", "").lower() for s in (profile.get("skills") or [])]
    skill_score, skill_details = compute_skill_score(job_skills, profile_skills)

    # 2. Seniority fit
    seniority_score = compute_seniority_score(
        job.get("seniority_level"),
        profile.get("experience_years", 0),
    )

    # 3. Salary alignment
    salary_score = compute_salary_score(
        job_min=job.get("salary_min"),
        job_max=job.get("salary_max"),
        profile_min=profile.get("target_salary_min"),
        profile_max=profile.get("target_salary_max"),
    )

    # 4. Recency
    recency_score = compute_recency_score(job.get("posted_at"))

    # 5. Company growth (normalized 0-1)
    company_growth_norm = min(company_hiring_score / 100.0, 1.0)

    # 6. Culture fit (placeholder — use embedding similarity when available)
    culture_fit = 0.5

    # Weighted aggregate
    total = (
        weights.get("skill_overlap", 0.30) * skill_score
        + weights.get("seniority_fit", 0.20) * seniority_score
        + weights.get("culture_fit", 0.15) * culture_fit
        + weights.get("company_growth_signal", 0.15) * company_growth_norm
        + weights.get("salary_alignment", 0.10) * salary_score
        + weights.get("recency_score", 0.10) * recency_score
    )

    match_score = round(min(total * 100, 100), 1)

    # Risk factors
    risk_factors = []
    if skill_score < 0.4:
        risk_factors.append("Low skill overlap with job requirements")
    if seniority_score < 0.3:
        risk_factors.append("Significant experience gap")
    if salary_score < 0.2 and salary_score >= 0:
        risk_factors.append("Salary range mismatch")

    # Strength factors
    strength_factors = []
    if skill_score > 0.7:
        strength_factors.append(f"Strong skill match ({int(skill_score * 100)}% overlap)")
    if seniority_score > 0.7:
        strength_factors.append("Good seniority alignment")
    if company_hiring_score > 60:
        strength_factors.append("Company is actively hiring")
    if recency_score > 0.8:
        strength_factors.append("Recently posted job")

    skill_coverage_pct = round(skill_score * 100, 1)

    return {
        "match_score": match_score,
        "skill_coverage_pct": skill_coverage_pct,
        "skill_overlap_score": round(skill_score, 3),
        "seniority_fit_score": round(seniority_score, 3),
        "salary_alignment_score": round(salary_score, 3),
        "recency_score": round(recency_score, 3),
        "company_growth_score": round(company_growth_norm, 3),
        "risk_factors": risk_factors,
        "strength_factors": strength_factors,
        "scoring_breakdown": {
            "skill_overlap": {
                "score": skill_score,
                "weight": weights.get("skill_overlap", 0.30),
                "weighted": skill_score * weights.get("skill_overlap", 0.30),
                "matched_skills": skill_details.get("matched", []),
                "missing_skills": skill_details.get("missing", []),
            },
            "seniority_fit": {
                "score": seniority_score,
                "weight": weights.get("seniority_fit", 0.20),
            },
            "salary_alignment": {
                "score": salary_score,
                "weight": weights.get("salary_alignment", 0.10),
            },
            "recency": {
                "score": recency_score,
                "weight": weights.get("recency_score", 0.10),
            },
        },
    }
