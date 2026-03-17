import logging
import os
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Central LLM content generation engine."""

    PROMPT_TEMPLATES = {
        "cover_letter": """Write a compelling cover letter for {name} applying for {job_title} at {company}.

Candidate background: {background}
Key matching skills: {matching_skills}
Tone: {tone}

Requirements:
- 3-4 paragraphs
- Professional but personable
- Highlight specific value for the role
- Do not use generic phrases like "I am writing to apply"
- End with a clear call to action

Write the cover letter:""",

        "recruiter_outreach": """Write a short, personalized recruiter outreach message from {sender_name} to a recruiter at {company} about the {job_title} role.

Sender background: {background}
Tone: {tone}

Requirements:
- Subject line (prefix with "Subject: ")
- 3-4 short paragraphs
- Professional and direct
- Show genuine interest in the company
- Clear ask at the end

Write the message:""",

        "referral_request": """Write a professional referral request from {sender_name} to {recipient_name} who works at {company}, asking for a referral for the {job_title} role.

Their relationship: {relationship}
Sender background: {background}

Requirements:
- Warm and personal opening
- Clear ask in first paragraph
- Explain why you're a good fit
- Make it easy to say yes
- Thank them regardless

Write the message:""",

        "linkedin_post": """Write a professional LinkedIn post for a job seeker in {field} with {experience_years} years of experience.

Topics to cover: {topics}
Tone: {tone}

Requirements:
- 3-5 paragraphs
- Start with a hook
- Add value or insight
- Personal and authentic
- End with a question or CTA
- Add 3-5 relevant hashtags

Write the post:""",

        "followup_email": """Write a polite follow-up email from {sender_name} to {company} about their {job_title} application submitted {days_ago} days ago.

Tone: {tone}

Requirements:
- Subject line (prefix with "Subject: ")
- Brief (2-3 paragraphs)
- Reaffirm interest
- Politely ask about timeline
- Professional sign-off

Write the email:""",

        "connection_note": """Write a personalized LinkedIn connection request note from {sender_name} to {recipient_name} at {company}.

Context: {context}
Tone: {tone}

Requirements:
- Under 300 characters (LinkedIn limit)
- Personal and specific
- Clear reason for connecting

Write the note:""",
    }

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
                from integrations.llm.router import get_llm_client
                self._llm = get_llm_client(task_type="primary")
            except Exception as e:
                logger.warning(f"LLM unavailable: {e}")
        return self._llm

    async def generate(
        self,
        content_type: str,
        job=None,
        target_person: Optional[str] = None,
        target_company: Optional[str] = None,
        tone: str = "professional",
        additional_context: Optional[str] = None,
        profile=None,
    ) -> Dict[str, Any]:
        """Generate content of the specified type."""
        llm = self._get_llm()

        if llm is None:
            return self._generate_fallback(content_type, job, target_person, target_company)

        template = self.PROMPT_TEMPLATES.get(content_type)
        if not template:
            return {"body": f"Draft {content_type} content", "subject": "", "model_used": "none"}

        # Build template variables
        vars = self._build_template_vars(
            content_type, job, target_person, target_company, tone, profile, additional_context
        )

        try:
            prompt = template.format(**vars)
            response = await llm.complete(prompt, max_tokens=600)

            # Extract subject if present
            subject = ""
            body = response
            if "Subject:" in response:
                lines = response.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("Subject:"):
                        subject = line.replace("Subject:", "").strip()
                        body = "\n".join(lines[i+1:]).strip()
                        break

            model_used = getattr(llm, "model_name", "unknown")
            return {"body": body, "subject": subject, "model_used": model_used}
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return self._generate_fallback(content_type, job, target_person, target_company)

    def _build_template_vars(self, content_type, job, target_person, target_company, tone, profile, context) -> dict:
        company = target_company or (job.company_name if job else "the company")
        job_title = (job.title if job else "the role")
        name = (profile.full_name if profile else "the candidate")
        background = "Experienced professional"
        experience_years = (profile.experience_years if profile else 3)
        skills = []
        if profile and profile.skills:
            skills = [s.get("name", "") if isinstance(s, dict) else str(s) for s in profile.skills[:6]]

        matching_skills = ", ".join(skills) if skills else "relevant technical skills"

        return {
            "name": name,
            "sender_name": name,
            "recipient_name": target_person or "colleague",
            "job_title": job_title,
            "company": company,
            "background": background,
            "matching_skills": matching_skills,
            "tone": tone,
            "field": "software engineering",
            "experience_years": experience_years,
            "topics": context or "career growth, technology trends",
            "relationship": "professional connection",
            "context": f"Interested in {company}",
            "days_ago": 7,
        }

    def _generate_fallback(self, content_type, job, target_person, target_company) -> dict:
        company = target_company or (job.company_name if job else "the company")
        job_title = (job.title if job else "the role")
        body = f"[Draft {content_type}]\n\nDear {target_person or 'Hiring Team'},\n\nI am reaching out regarding the {job_title} opportunity at {company}.\n\n[Personalize this draft before sending]\n\nBest regards"
        return {"body": body, "subject": f"Re: {job_title} at {company}", "model_used": "fallback"}
