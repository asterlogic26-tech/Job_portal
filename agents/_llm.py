"""
Lightweight LLM helpers shared by all agents.
Gracefully degrades when no API key is configured.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def call_llm(prompt: str, max_tokens: int = 600, task_type: str = "cheap") -> str:
    """Call the configured LLM and return raw text.

    Falls back to empty string on any error so agents can use rule-based
    fallback paths rather than crashing the pipeline.
    """
    try:
        from integrations.llm.router import get_llm_client
        client = get_llm_client(task_type=task_type)
        if client is None:
            return ""
        return await client.complete(prompt, max_tokens=max_tokens)
    except Exception as exc:
        logger.warning("LLM call failed (%s): %s", task_type, exc)
        return ""


def extract_json(text: str) -> Dict[str, Any]:
    """Extract the first JSON object found in an LLM response.

    Returns an empty dict if parsing fails.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def normalize_skills(skills: list) -> list[str]:
    """Normalize a skill list to lowercase strings.

    Handles both ``["Python", ...]`` and ``[{"name": "Python"}, ...]`` formats.
    """
    result: list[str] = []
    for s in skills or []:
        if isinstance(s, str):
            v = s.strip().lower()
            if v:
                result.append(v)
        elif isinstance(s, dict):
            v = (s.get("name") or s.get("skill") or "").strip().lower()
            if v:
                result.append(v)
    return result
