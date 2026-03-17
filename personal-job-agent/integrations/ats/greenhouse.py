import logging
import httpx
from typing import Optional, List, Dict, Any

from integrations.ats.base_ats import BaseATSClient

logger = logging.getLogger(__name__)

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseClient(BaseATSClient):
    """Greenhouse public job board API client."""

    async def get_jobs(self, company_slug: str, limit: int = 50) -> List[Dict[str, Any]]:
        url = f"{GREENHOUSE_API_BASE}/{company_slug}/jobs?content=true"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers={"User-Agent": "PersonalJobAgent/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("jobs", [])[:limit]
                logger.warning(f"Greenhouse API returned {resp.status_code} for {company_slug}")
                return []
        except Exception as e:
            logger.error(f"Greenhouse API error for {company_slug}: {e}")
            return []

    async def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return None  # Detail in main jobs endpoint for Greenhouse

    def normalize_job(self, raw: Dict, company_name: str) -> Dict:
        """Normalize a Greenhouse job to our schema."""
        content = raw.get("content", "")
        location = ""
        offices = raw.get("offices", [])
        if offices:
            location = offices[0].get("name", "")

        return {
            "external_id": str(raw.get("id", "")),
            "source": "greenhouse_api",
            "title": raw.get("title", ""),
            "company_name": company_name,
            "description_raw": content,
            "apply_url": raw.get("absolute_url", ""),
            "location": location,
            "posted_at": raw.get("updated_at"),
            "metadata": {"department": raw.get("departments", [{}])[0].get("name", "") if raw.get("departments") else ""},
        }
