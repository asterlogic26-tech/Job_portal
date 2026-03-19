import math
from typing import Optional
from datetime import datetime, timezone


def compute_recency_score(posted_at: Optional[datetime], half_life_days: int = 14) -> float:
    """Exponential decay score based on posting age."""
    if posted_at is None:
        return 0.5

    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    age_days = (now - posted_at).days

    if age_days < 0:
        return 1.0

    decay = math.exp(-math.log(2) * age_days / half_life_days)
    return round(max(0.0, min(1.0, decay)), 3)
