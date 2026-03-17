import re
from typing import Dict

TITLE_NORMALIZATIONS: Dict[str, str] = {
    r"sr\.?\s+": "Senior ",
    r"jr\.?\s+": "Junior ",
    r"swe\b": "Software Engineer",
    r"sde\b": "Software Development Engineer",
    r"mle\b": "Machine Learning Engineer",
    r"ml\s+eng": "Machine Learning Engineer",
    r"full.?stack": "Full Stack",
    r"frontend|front-end|front end": "Frontend",
    r"backend|back-end|back end": "Backend",
    r"devops|dev.?ops": "DevOps",
}


def normalize_title(raw_title: str) -> str:
    """Normalize a job title to a canonical form."""
    title = raw_title.strip()
    title_lower = title.lower()

    for pattern, replacement in TITLE_NORMALIZATIONS.items():
        title_lower = re.sub(pattern, replacement.lower(), title_lower)

    # Capitalize properly
    words = title_lower.split()
    normalized = " ".join(w.capitalize() for w in words)
    return normalized
