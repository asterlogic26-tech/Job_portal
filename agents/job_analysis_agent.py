"""
Job Analysis Agent

Analyzes a job description to extract structured information.
Uses an LLM for deep extraction when available; falls back to
using the job's existing structured fields otherwise.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from agents.base import BaseAgent
from agents._llm import call_llm, extract_json, normalize_skills

_ANALYSIS_PROMPT = """\
Analyze the following job description and extract structured information.

Job Title: {title}
Company: {company}
Description:
{description}

Return ONLY a valid JSON object (no markdown fences) with exactly these keys:
{{
  "required_skills": ["skill1", "skill2"],
  "experience_level": "junior|mid|senior|staff|lead|director",
  "job_summary": "2-3 sentence summary of the role",
  "key_requirements": ["requirement 1", "requirement 2", "requirement 3", "requirement 4", "requirement 5"]
}}
"""


class JobAnalysisAgent(BaseAgent):
    """Analyze a job description and return structured insights."""

    name = "job_analysis"

    def validate(self, input_data: Dict[str, Any]) -> bool:
        return bool(input_data.get("title") or input_data.get("description"))

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        title = input_data.get("title", "Unknown Role")
        company = input_data.get("company_name", "Unknown Company")
        description = input_data.get("description", "")
        existing_skills = normalize_skills(
            input_data.get("required_skills", [])
        )
        existing_seniority = input_data.get("seniority_level", "unknown")

        # Attempt LLM-based analysis
        llm_result: Dict[str, Any] = {}
        if description:
            prompt = _ANALYSIS_PROMPT.format(
                title=title, company=company, description=description[:3000]
            )
            raw = await call_llm(prompt, max_tokens=500, task_type="cheap")
            if raw:
                llm_result = extract_json(raw)

        # Merge LLM result with existing structured fields
        required_skills: List[str] = (
            normalize_skills(llm_result.get("required_skills", []))
            or existing_skills
        )
        experience_level: str = (
            llm_result.get("experience_level")
            or existing_seniority
            or "unknown"
        )
        job_summary: str = (
            llm_result.get("job_summary")
            or f"{title} at {company}"
        )
        key_requirements: List[str] = (
            llm_result.get("key_requirements")
            or _extract_requirements_from_text(description)
        )

        return {
            "required_skills": required_skills,
            "experience_level": experience_level,
            "job_summary": job_summary,
            "key_requirements": key_requirements[:8],  # cap at 8
        }


def _extract_requirements_from_text(text: str) -> List[str]:
    """Extract bullet-point requirements from raw description text."""
    requirements = []
    for line in text.split("\n"):
        line = line.strip()
        # Lines that look like bullet points
        if re.match(r"^[\-\*•·]\s+.{10,}", line):
            cleaned = re.sub(r"^[\-\*•·]\s+", "", line)
            requirements.append(cleaned)
        if len(requirements) >= 5:
            break
    return requirements
