"""
Resume Agent

Generates a tailored resume summary and skill highlights optimised
for a specific job, using the LLM content generator.
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent
from agents._llm import call_llm, normalize_skills

_RESUME_PROMPT = """\
Write a tailored resume professional summary for {name} applying for {job_title} at {company}.

Candidate background:
- Experience: {experience_years} years
- Skills: {profile_skills}

Key skills that match this job: {matched_skills}
Skills to address/de-emphasize: {missing_skills}

Requirements:
- 3-4 sentences professional summary
- Lead with years of experience and strongest relevant skills
- Weave in the matched skills naturally
- End with value proposition for this specific role
- Do NOT include generic phrases like "results-driven" or "passionate"

Return only the professional summary text, no labels or headers.
"""


class ResumeAgent(BaseAgent):
    """Generate a tailored resume summary and skill highlights."""

    name = "resume"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        profile = input_data.get("profile", {})
        matching = input_data.get("matching", {})
        job_analysis = input_data.get("job_analysis", {})

        name = profile.get("full_name", "Candidate")
        experience_years = profile.get("experience_years", 0)
        job_title = input_data.get("title", "the role")
        company = input_data.get("company_name", "the company")

        # Normalize profile skills to strings
        profile_skills: List[str] = normalize_skills(profile.get("skills", []))
        matched_skills: List[str] = matching.get("matched_skills", [])
        missing_skills: List[str] = matching.get("missing_skills", [])

        # Highlighted skills = matched skills + top profile skills not in missing
        highlighted_skills: List[str] = list(
            dict.fromkeys(matched_skills + [s for s in profile_skills if s not in missing_skills])
        )[:10]

        # LLM-generated tailored summary
        prompt = _RESUME_PROMPT.format(
            name=name,
            job_title=job_title,
            company=company,
            experience_years=experience_years,
            profile_skills=", ".join(profile_skills[:12]) or "not provided",
            matched_skills=", ".join(matched_skills[:8]) or "various skills",
            missing_skills=", ".join(missing_skills[:5]) or "none",
        )
        custom_resume = await call_llm(prompt, max_tokens=300, task_type="cheap")

        if not custom_resume:
            custom_resume = (
                f"Experienced {job_title} with {experience_years} years of expertise "
                f"in {', '.join(highlighted_skills[:4]) or 'relevant technologies'}. "
                f"Proven track record delivering impactful solutions with a strong focus on "
                f"quality and collaboration. Eager to contribute to {company}'s mission."
            )

        return {
            "custom_resume": custom_resume.strip(),
            "highlighted_skills": highlighted_skills,
        }
