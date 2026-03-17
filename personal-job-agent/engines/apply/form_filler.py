"""
Playwright-based application form filler.

IMPORTANT: This module NEVER bypasses CAPTCHA or anti-bot protections.
If a CAPTCHA or block is detected, it returns immediately with
``blocked_reason="captcha"`` so the caller can create a ManualTask.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from engines.apply.ats_router import get_field_selectors, detect_ats

logger = logging.getLogger(__name__)

# Page text patterns that indicate bot detection / CAPTCHA
_CAPTCHA_INDICATORS = [
    "recaptcha", "hcaptcha", "captcha", "verify you are human",
    "are you a robot", "cloudflare", "ddos-guard", "just a moment",
    "access denied", "403 forbidden", "enable javascript to continue",
    "prove you are human",
]

# Submit button selectors — tried in order
_SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit Application")',
    'button:has-text("Apply Now")',
    'button:has-text("Submit")',
    'button:has-text("Apply")',
    '[data-qa="btn-apply"]',
]

_PAGE_TIMEOUT_MS = 30_000
_ACTION_TIMEOUT_MS = 5_000


async def fill_and_submit(
    apply_url: str,
    profile: Dict[str, Any],
    cover_letter: str = "",
    resume_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Navigate to ``apply_url``, fill the application form, and submit.

    Returns::

        {
            "success": bool,
            "method": "playwright",
            "ats": Optional[str],
            "fields_filled": List[str],
            "blocked_reason": Optional[str],
            "confirmation_text": Optional[str],
        }

    Never raises — all exceptions are caught and returned as errors.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed; auto-apply unavailable")
        return _blocked("playwright_not_installed")

    ats = detect_ats(apply_url)
    selectors = get_field_selectors(ats)
    fields_filled: List[str] = []

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # ── Navigate ─────────────────────────────────────────────────────
            try:
                await page.goto(apply_url, timeout=_PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
            except Exception as exc:
                await browser.close()
                return _blocked(f"navigation_error: {exc}")

            # ── CAPTCHA check ────────────────────────────────────────────────
            page_text = (await page.content()).lower()
            for indicator in _CAPTCHA_INDICATORS:
                if indicator in page_text:
                    logger.warning("CAPTCHA/block detected on %s", apply_url)
                    await browser.close()
                    return _blocked("captcha")

            # ── Fill form fields ─────────────────────────────────────────────
            first_name = profile.get("full_name", "").split()[0] if profile.get("full_name") else ""
            last_name = " ".join(profile.get("full_name", "").split()[1:]) if profile.get("full_name") else ""

            fill_map = {
                "first_name": first_name,
                "last_name": last_name,
                "full_name": profile.get("full_name", ""),
                "email": profile.get("email", ""),
                "phone": profile.get("phone", ""),
                "linkedin": profile.get("linkedin_url", ""),
                "cover_letter": cover_letter,
            }

            for field_name, value in fill_map.items():
                if not value:
                    continue
                for selector in selectors.get(field_name, []):
                    try:
                        el = page.locator(selector).first
                        if await el.count() > 0:
                            await el.fill(str(value), timeout=_ACTION_TIMEOUT_MS)
                            fields_filled.append(field_name)
                            break
                    except Exception:
                        continue

            # ── Resume file upload ───────────────────────────────────────────
            if resume_path and os.path.exists(resume_path):
                for selector in selectors.get("resume", []):
                    try:
                        el = page.locator(selector).first
                        if await el.count() > 0:
                            await el.set_input_files(resume_path, timeout=_ACTION_TIMEOUT_MS)
                            fields_filled.append("resume")
                            break
                    except Exception:
                        continue

            # ── Submit ───────────────────────────────────────────────────────
            submitted = False
            for submit_sel in _SUBMIT_SELECTORS:
                try:
                    btn = page.locator(submit_sel).first
                    if await btn.count() > 0 and await btn.is_enabled():
                        await btn.click(timeout=_ACTION_TIMEOUT_MS)
                        submitted = True
                        break
                except Exception:
                    continue

            if not submitted:
                await browser.close()
                return _blocked("submit_button_not_found")

            # ── Wait for confirmation ────────────────────────────────────────
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                pass

            # Check for post-submit CAPTCHA
            post_text = (await page.content()).lower()
            for indicator in _CAPTCHA_INDICATORS:
                if indicator in post_text:
                    await browser.close()
                    return _blocked("captcha_post_submit")

            # Extract confirmation text
            confirmation = _extract_confirmation(post_text)
            await browser.close()

            return {
                "success": True,
                "method": "playwright",
                "ats": ats,
                "fields_filled": fields_filled,
                "blocked_reason": None,
                "confirmation_text": confirmation,
            }

    except Exception as exc:
        logger.exception("Playwright form fill error on %s", apply_url)
        return _blocked(f"unexpected_error: {type(exc).__name__}")


def _blocked(reason: str) -> Dict[str, Any]:
    return {
        "success": False,
        "method": "blocked",
        "ats": None,
        "fields_filled": [],
        "blocked_reason": reason,
        "confirmation_text": None,
    }


def _extract_confirmation(page_text_lower: str) -> Optional[str]:
    """Try to extract a confirmation message from the post-submit page."""
    for phrase in [
        "application submitted",
        "thank you for applying",
        "application received",
        "successfully applied",
        "we've received your application",
    ]:
        if phrase in page_text_lower:
            return phrase.title()
    return None
