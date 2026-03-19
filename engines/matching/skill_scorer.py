from typing import List, Tuple, Dict


def compute_skill_score(
    job_skills: List[str], profile_skills: List[str]
) -> Tuple[float, Dict]:
    """
    Compute skill overlap score.
    Returns (score 0-1, details dict)
    """
    if not job_skills:
        return 0.7, {"matched": [], "missing": []}

    job_set = set(s.lower().strip() for s in job_skills)
    profile_set = set(s.lower().strip() for s in profile_skills)

    matched = list(job_set & profile_set)
    missing = list(job_set - profile_set)

    score = len(matched) / len(job_set) if job_set else 0.0

    return score, {"matched": matched, "missing": missing[:10]}
