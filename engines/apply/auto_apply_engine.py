"""
Auto-Apply Engine — orchestrates the end-to-end application submission.

Flow:
  1. Check if the apply URL is accessible / supported
  2. Generate + store a tailored cover letter
  3. Download resume from MinIO if available
  4. Attempt Playwright form-fill
  5. Return a structured result the caller uses to:
       • Update Application status
       • Create ManualTask + Notification (if blocked)
       • Log to ApplicationEvent timeline

HARD CONTRACT: Never bypass CAPTCHA or anti-bot systems.
"""
from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Dict, Optional

from engines.apply.ats_router import detect_ats, is_form_fill_supported

logger = logging.getLogger(__name__)


async def run_auto_apply(
    apply_url: str,
    profile: Dict[str, Any],
    job: Dict[str, Any],
    cover_letter: str = "",
    resume_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point — attempt to auto-apply for a job.

    Args:
        apply_url:    Direct application URL.
        profile:      User profile dict (name, email, phone, linkedin_url, …).
        job:          Job dict (title, company_name, description, …).
        cover_letter: Pre-generated cover letter text.
        resume_path:  Local path to resume PDF/DOCX, or None.

    Returns::

        {
            "applied":            bool,
            "apply_method":       "playwright" | "blocked" | "error",
            "ats_detected":       Optional[str],
            "fields_filled":      List[str],
            "blocked":            bool,
            "blocked_reason":     Optional[str],
            "direct_apply_url":   str,   # always == apply_url for caller
            "confidence":         int,   # 0-100 estimate we actually applied
        }
    """
    if not apply_url:
        logger.warning("auto_apply called without apply_url for job %s", job.get("title"))
        return _result(False, "blocked", blocked_reason="no_apply_url", direct_url=apply_url)

    ats = detect_ats(apply_url)

    # Check if this ATS type is known to block automated submission
    if not is_form_fill_supported(apply_url):
        logger.info("ATS '%s' does not support form-fill: %s", ats, apply_url)
        return _result(False, "blocked", blocked_reason=f"ats_not_supported:{ats}", direct_url=apply_url)

    # Download resume if given as a URL
    local_resume = resume_path
    if not local_resume and profile.get("resume_url"):
        local_resume = await _download_resume(profile["resume_url"])

    # Attempt form fill
    from engines.apply.form_filler import fill_and_submit
    result = await fill_and_submit(
        apply_url=apply_url,
        profile=profile,
        cover_letter=cover_letter,
        resume_path=local_resume,
    )

    success = result.get("success", False)
    blocked_reason = result.get("blocked_reason")

    # Estimate confidence: more fields filled → higher confidence
    filled_count = len(result.get("fields_filled", []))
    confidence = min(60 + filled_count * 8, 95) if success else 0

    return {
        "applied": success,
        "apply_method": result.get("method", "error"),
        "ats_detected": result.get("ats"),
        "fields_filled": result.get("fields_filled", []),
        "blocked": not success,
        "blocked_reason": blocked_reason,
        "direct_apply_url": apply_url,
        "confidence": confidence,
        "confirmation_text": result.get("confirmation_text"),
    }


def _result(
    success: bool,
    method: str,
    blocked_reason: Optional[str] = None,
    direct_url: str = "",
) -> Dict[str, Any]:
    return {
        "applied": success,
        "apply_method": method,
        "ats_detected": None,
        "fields_filled": [],
        "blocked": not success,
        "blocked_reason": blocked_reason,
        "direct_apply_url": direct_url,
        "confidence": 0,
        "confirmation_text": None,
    }


async def _download_resume(resume_url: str) -> Optional[str]:
    """Download resume from URL to a temp file. Returns local path or None."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(resume_url)
            if resp.status_code == 200:
                suffix = ".pdf" if "pdf" in resume_url.lower() else ".docx"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tmp.write(resp.content)
                tmp.close()
                return tmp.name
    except Exception as exc:
        logger.warning("Could not download resume from %s: %s", resume_url, exc)
    return None
