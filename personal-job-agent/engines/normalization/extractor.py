import json
import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class JobEntityExtractor:
    """Extract structured entities from raw job description text using LLM."""

    EXTRACTION_PROMPT = """You are a job data extraction assistant. Extract structured information from the following job posting.

Return ONLY a valid JSON object with these fields:
- title: string (job title)
- title_normalized: string (canonical job title, e.g. "Senior Software Engineer")
- seniority_level: string (one of: intern, junior, mid, senior, staff, principal, lead, manager, director, vp)
- employment_type: string (one of: full_time, part_time, contract, internship, freelance)
- remote_policy: string (one of: remote, hybrid, onsite, any)
- location: string (city/country or "Remote")
- salary_min: integer or null (annual USD)
- salary_max: integer or null (annual USD)
- salary_raw: string (original salary text or null)
- skills_required: array of objects [{name: string, category: string}]
- skills_preferred: array of objects [{name: string, category: string}]
- description_markdown: string (clean markdown version, max 1000 chars)
- responsibilities: array of strings (top 5)
- company_name: string

Job Posting:
---
{raw_text}
---

Return only the JSON, no explanation."""

    def __init__(self):
        self._llm_client = None

    def _get_llm(self):
        if self._llm_client is None:
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
                from integrations.llm.router import get_llm_client
                self._llm_client = get_llm_client(task_type="cheap")
            except Exception as e:
                logger.warning(f"LLM client unavailable: {e}")
        return self._llm_client

    async def extract(self, raw_text: str, fallback_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract entities from raw job text."""
        llm = self._get_llm()

        if llm is None:
            return self._rule_based_extract(raw_text, fallback_data or {})

        try:
            prompt = self.EXTRACTION_PROMPT.format(raw_text=raw_text[:3000])
            response = await llm.complete(prompt, max_tokens=1000)
            # Parse JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")

        return self._rule_based_extract(raw_text, fallback_data or {})

    def _rule_based_extract(self, text: str, fallback: Dict) -> Dict:
        """Fallback rule-based extraction."""
        # Seniority detection
        seniority = "mid"
        text_lower = text.lower()
        if any(w in text_lower for w in ["senior", "sr.", "sr "]):
            seniority = "senior"
        elif any(w in text_lower for w in ["junior", "jr.", "entry level", "entry-level"]):
            seniority = "junior"
        elif any(w in text_lower for w in ["staff", "principal"]):
            seniority = "staff"
        elif any(w in text_lower for w in ["lead", "tech lead"]):
            seniority = "lead"
        elif any(w in text_lower for w in ["manager", "engineering manager"]):
            seniority = "manager"

        # Remote detection
        remote_policy = "onsite"
        if "remote" in text_lower:
            if "hybrid" in text_lower:
                remote_policy = "hybrid"
            else:
                remote_policy = "remote"

        # Employment type
        employment_type = "full_time"
        if "contract" in text_lower:
            employment_type = "contract"
        elif "part-time" in text_lower or "part time" in text_lower:
            employment_type = "part_time"
        elif "intern" in text_lower:
            employment_type = "internship"

        # Skills extraction (common tech keywords)
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
            "AWS", "GCP", "Azure", "FastAPI", "Django", "Flask", "Go", "Rust",
            "Java", "Scala", "Kotlin", "Swift", "C++", "C#", "Ruby", "Rails",
            "GraphQL", "REST", "gRPC", "Kafka", "Spark", "Machine Learning",
            "PyTorch", "TensorFlow", "Pandas", "Git", "CI/CD", "Linux"
        ]
        found_skills = [
            {"name": skill, "category": "technical"}
            for skill in common_skills
            if skill.lower() in text_lower
        ]

        # Salary extraction
        salary_pattern = r'\$(\d+)k?\s*[-\u2013to]+\s*\$?(\d+)k?'
        salary_match = re.search(salary_pattern, text_lower)
        salary_min, salary_max, salary_raw = None, None, None
        if salary_match:
            s1, s2 = int(salary_match.group(1)), int(salary_match.group(2))
            salary_min = s1 * 1000 if s1 < 1000 else s1
            salary_max = s2 * 1000 if s2 < 1000 else s2
            salary_raw = salary_match.group(0)

        # Clean text to markdown
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        desc_markdown = clean_text[:800]

        return {
            "title": fallback.get("title", ""),
            "title_normalized": fallback.get("title", ""),
            "seniority_level": seniority,
            "employment_type": employment_type,
            "remote_policy": remote_policy,
            "location": fallback.get("location", ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_raw": salary_raw,
            "skills_required": found_skills[:10],
            "skills_preferred": [],
            "description_markdown": desc_markdown,
            "responsibilities": [],
            "company_name": fallback.get("company_name", ""),
        }
