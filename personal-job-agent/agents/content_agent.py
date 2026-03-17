"""
Content Agent

Generates a daily professional LinkedIn post for the user, tailored
to their field, experience, and current job-search context.
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent

_DEFAULT_TOPICS = [
    "lessons learned from recent technical challenges",
    "career growth tips for software engineers",
    "open source contributions and side projects",
    "remote work productivity habits",
    "AI tools that improve developer workflow",
]


class ContentAgent(BaseAgent):
    """Generate a professional LinkedIn post using the LLM generator."""

    name = "content"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from engines.content.generator import ContentGenerator

        profile = input_data.get("profile", {})
        job_analysis = input_data.get("job_analysis", {})

        experience_years = profile.get("experience_years", 3)
        top_skills: List[str] = []
        for s in profile.get("skills", [])[:4]:
            if isinstance(s, dict):
                top_skills.append(s.get("name", ""))
            elif isinstance(s, str):
                top_skills.append(s)

        # Choose topics relevant to the current job search context
        job_summary = job_analysis.get("job_summary", "")
        if job_summary:
            topics = f"career pivot, {', '.join(top_skills[:2]) or 'engineering'}, job search learnings"
        else:
            topics = ", ".join(_DEFAULT_TOPICS[:2])

        profile_stub = _ProfileStub(
            full_name=profile.get("full_name", ""),
            experience_years=experience_years,
            skills=profile.get("skills", []),
        )

        generator = ContentGenerator()
        result = await generator.generate(
            content_type="linkedin_post",
            tone="professional",
            profile=profile_stub,
            additional_context=topics,
        )

        body = result.get("body", "")
        if not body:
            body = _fallback_post(top_skills, experience_years)

        return {
            "linkedin_post": body.strip(),
            "model_used": result.get("model_used", "fallback"),
            "suggested_topics": topics,
        }


def _fallback_post(skills: List[str], years: int) -> str:
    skill_str = ", ".join(skills[:3]) if skills else "software engineering"
    return (
        f"After {years} years in {skill_str}, the most important lesson I've learned is "
        f"that consistent learning beats occasional brilliance.\n\n"
        f"Every week I try to ship something, learn something, and share something.\n\n"
        f"What's one habit that's had the biggest impact on your career growth?\n\n"
        f"#SoftwareEngineering #CareerGrowth #LearningEveryDay"
    )


class _ProfileStub:
    def __init__(self, full_name: str, experience_years: int, skills: list):
        self.full_name = full_name
        self.experience_years = experience_years
        self.skills = skills
