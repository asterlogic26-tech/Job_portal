from typing import Optional


def compute_salary_score(
    job_min: Optional[int],
    job_max: Optional[int],
    profile_min: Optional[int],
    profile_max: Optional[int],
) -> float:
    """Score salary range overlap."""
    if not any([job_min, job_max, profile_min, profile_max]):
        return 0.5  # Unknown — neutral

    # If only partial info, be optimistic
    if not profile_min or not profile_max:
        return 0.5
    if not job_min and not job_max:
        return 0.5

    j_min = job_min or job_max or 0
    j_max = job_max or job_min or 0
    p_min = profile_min
    p_max = profile_max

    # Check overlap
    overlap_start = max(j_min, p_min)
    overlap_end = min(j_max, p_max)

    if overlap_end < overlap_start:
        # No overlap — compute distance penalty
        if p_min > j_max:  # Profile wants more
            gap = p_min - j_max
            penalty = gap / p_min
            return max(0.0, 0.5 - penalty)
        else:  # Job pays more — good for user
            return 0.8
    else:
        overlap = overlap_end - overlap_start
        job_range = max(j_max - j_min, 1)
        profile_range = max(p_max - p_min, 1)
        overlap_ratio = overlap / max(job_range, profile_range)
        return min(1.0, 0.5 + overlap_ratio * 0.5)
