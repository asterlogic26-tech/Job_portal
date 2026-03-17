from typing import Optional

SENIORITY_YEAR_MAP = {
    "intern": (0, 1),
    "junior": (0, 2),
    "mid": (2, 5),
    "senior": (5, 10),
    "staff": (7, 15),
    "principal": (10, 20),
    "lead": (5, 15),
    "manager": (5, 15),
    "director": (10, 20),
    "vp": (15, 30),
}


def compute_seniority_score(
    job_seniority: Optional[str], user_years: int
) -> float:
    """Score how well user's experience matches the job's seniority."""
    if not job_seniority:
        return 0.7  # Unknown — neutral

    range_min, range_max = SENIORITY_YEAR_MAP.get(job_seniority.lower(), (2, 5))

    if range_min <= user_years <= range_max:
        return 1.0
    elif user_years < range_min:
        gap = range_min - user_years
        return max(0.0, 1.0 - (gap / range_min) * 0.5)
    else:  # Over-qualified
        excess = user_years - range_max
        return max(0.5, 1.0 - (excess / 10) * 0.3)
