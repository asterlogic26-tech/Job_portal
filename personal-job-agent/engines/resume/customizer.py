import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ResumeCustomizer:
    """Tailors a resume to a specific job using LLM."""

    async def customize(
        self,
        profile,
        job,
        master_resume=None,
        tone: str = "professional",
    ) -> Dict[str, Any]:
        """Generate a tailored resume JSON."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
            from integrations.llm.router import get_llm_client
            llm = get_llm_client(task_type="primary")
        except Exception:
            llm = None

        # Build base content from profile
        skills = profile.skills if profile and profile.skills else []
        skill_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills]

        # Get job required skills
        job_skills = []
        if job and job.skills_required:
            job_skills = [s.get("name", "") if isinstance(s, dict) else str(s) for s in job.skills_required]

        # Keyword analysis
        skill_set = set(s.lower() for s in skill_names)
        job_skill_set = set(s.lower() for s in job_skills)
        matched = list(skill_set & job_skill_set)
        missing = list(job_skill_set - skill_set)

        # Generate summary
        summary = await self._generate_summary(profile, job, llm, tone)

        # ATS score simulation
        ats_score = len(matched) / max(len(job_skill_set), 1) * 100 if job_skill_set else 70.0

        return {
            "summary": summary,
            "skills_highlighted": skill_names[:15],
            "keywords_matched": matched[:20],
            "keywords_missing": missing[:10],
            "ats_score": round(ats_score, 1),
            "tone": tone,
            "tailored_for": {
                "title": job.title if job else "",
                "company": job.company_name if job else "",
            },
        }

    async def _generate_summary(self, profile, job, llm, tone: str) -> str:
        """Generate a tailored professional summary."""
        if not profile or not job:
            return "Experienced professional seeking new opportunities."

        if llm is None:
            return (
                f"{profile.experience_years or 'Experienced'}-year professional "
                f"with expertise in {', '.join([s.get('name', '') if isinstance(s, dict) else str(s) for s in (profile.skills or [])[:3]])}. "
                f"Seeking {job.title} role at {job.company_name or 'your company'}."
            )

        prompt = f"""Write a professional resume summary in {tone} tone for:
Name: {profile.full_name}
Current title: {profile.current_title}
Years of experience: {profile.experience_years}
Key skills: {', '.join([s.get('name','') if isinstance(s, dict) else str(s) for s in (profile.skills or [])[:8]])}
Applying for: {job.title} at {job.company_name or 'the company'}

Write 2-3 sentences. Be specific and achievement-focused. Do not use "I"."""

        try:
            return await llm.complete(prompt, max_tokens=200)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Experienced {profile.current_title or 'professional'} with {profile.experience_years} years of experience."
