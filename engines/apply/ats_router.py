"""
ATS Router — detect which Applicant Tracking System a URL belongs to,
and determine whether automated form-fill is supported.
"""
from __future__ import annotations

import re
from typing import Optional

# Pattern → ATS name. Order matters: more specific first.
_ATS_PATTERNS: list[tuple[str, str]] = [
    (r"boards\.greenhouse\.io", "greenhouse"),
    (r"greenhouse\.io", "greenhouse"),
    (r"jobs\.lever\.co", "lever"),
    (r"lever\.co", "lever"),
    (r"app\.ashbyhq\.com", "ashby"),
    (r"ashbyhq\.com", "ashby"),
    (r"jobs\.workable\.com", "workable"),
    (r"workable\.com/jobs", "workable"),
    (r"smartrecruiters\.com", "smartrecruiters"),
    (r"breezyhr\.com", "breezy"),
    (r"recruitee\.com", "recruitee"),
    (r"bamboohr\.com", "bamboo"),
    (r"myworkdayjobs\.com", "workday"),
    (r"workday\.com", "workday"),
    (r"taleo\.net", "taleo"),
    (r"icims\.com", "icims"),
    (r"jobvite\.com", "jobvite"),
    (r"successfactors\.eu|successfactors\.com", "successfactors"),
]

# ATS systems we can fill forms on automatically
_SUPPORTED_ATS: frozenset[str] = frozenset(
    {"greenhouse", "lever", "ashby", "workable", "breezy", "recruitee"}
)

# ATS systems that almost always block automated submission (SSO, CAPTCHA heavy)
_BLOCKED_ATS: frozenset[str] = frozenset(
    {"workday", "taleo", "icims", "successfactors", "jobvite"}
)


def detect_ats(url: str) -> Optional[str]:
    """Return the ATS provider name if the URL matches a known pattern."""
    if not url:
        return None
    for pattern, name in _ATS_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return name
    return None


def is_form_fill_supported(url: str) -> bool:
    """Return True if automated form-fill is worth attempting for this URL."""
    ats = detect_ats(url)
    if ats in _BLOCKED_ATS:
        return False
    # Supported ATS or unknown (try direct form fill)
    return ats in _SUPPORTED_ATS or ats is None


def get_field_selectors(ats: Optional[str]) -> dict[str, list[str]]:
    """Return CSS selectors tuned for a specific ATS, falling back to generic."""
    greenhouse = {
        "first_name": ['#first_name', 'input[name="job_application[first_name]"]'],
        "last_name": ['#last_name', 'input[name="job_application[last_name]"]'],
        "email": ['#email', 'input[name="job_application[email]"]'],
        "phone": ['#phone', 'input[name="job_application[phone]"]'],
        "resume": ['input[type="file"][name*="resume" i]', '#resume_text'],
        "cover_letter": ['textarea[name*="cover" i]', '#cover_letter_text'],
        "linkedin": ['input[name*="linkedin" i]'],
    }
    lever = {
        "full_name": ['input[name="name"]'],
        "email": ['input[name="email"]'],
        "phone": ['input[name="phone"]'],
        "resume": ['input[type="file"]'],
        "cover_letter": ['textarea[name*="comments" i]', 'textarea[name*="cover" i]'],
        "linkedin": ['input[name*="urls[LinkedIn]" i]', 'input[name*="linkedin" i]'],
    }
    generic = {
        "first_name": [
            'input[name*="first_name" i]', 'input[name*="firstName" i]',
            'input[placeholder*="first name" i]', 'input[id*="first_name" i]',
            'input[autocomplete="given-name"]',
        ],
        "last_name": [
            'input[name*="last_name" i]', 'input[name*="lastName" i]',
            'input[placeholder*="last name" i]', 'input[id*="last_name" i]',
            'input[autocomplete="family-name"]',
        ],
        "full_name": [
            'input[name="name" i]', 'input[placeholder*="full name" i]',
            'input[autocomplete="name"]',
        ],
        "email": [
            'input[type="email"]', 'input[name="email" i]',
            'input[placeholder*="email" i]', 'input[autocomplete="email"]',
        ],
        "phone": [
            'input[type="tel"]', 'input[name*="phone" i]',
            'input[placeholder*="phone" i]', 'input[autocomplete="tel"]',
        ],
        "linkedin": [
            'input[name*="linkedin" i]', 'input[placeholder*="linkedin" i]',
            'input[id*="linkedin" i]',
        ],
        "resume": ['input[type="file"][name*="resume" i]', 'input[type="file"]'],
        "cover_letter": [
            'textarea[name*="cover" i]', 'textarea[id*="cover" i]',
            'textarea[placeholder*="cover" i]', 'textarea[name*="letter" i]',
            'textarea[placeholder*="additional" i]',
        ],
    }
    mapping = {"greenhouse": greenhouse, "lever": lever}
    return mapping.get(ats or "", generic)
