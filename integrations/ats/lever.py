import logging
import httpx
from typing import Optional, List, Dict, Any

from integrations.ats.base_ats import BaseATSClient

logger = logging.getLogger(__name__)

LEVER_API_BASE = "https://api.lever.co/v0/postings"


class LeverClient(BaseATSClient):
    """Lever public job board API client."""

    async def get_jobs(self, company_slug: str, limit: int = 50) -> List[Dict[str, Any]]:
        url = f"{LEVER_API_BASE}/{company_slug}?mode=json&limit={limit}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers={"User-Agent": "PersonalJobAgent/1.0"})
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"Lever API returned {resp.status_code} for {company_slug}")
                return []
        except Exception as e:
            logger.error(f"Lever API error for {company_slug}: {e}")
            return []

    async def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        return None

    def normalize_job(self, raw: Dict, company_name: str) -> Dict:
        """Normalize a Lever job to our schema."""
        categories = raw.get("categories", {})
        lists = raw.get("lists", [])
        description_parts = [raw.get("descriptionPlain", "")]
        for item in lists:
            description_parts.append(item.get("content", ""))

        return {
            "external_id": raw.get("id", ""),
            "source": "lever_api",
            "title": raw.get("text", ""),
            "company_name": company_name,
            "description_raw": "\n".join(description_parts),
            "apply_url": raw.get("applyUrl", ""),
            "location": categories.get("location", ""),
            "remote_policy": "remote" if "remote" in categories.get("location", "").lower() else None,
            "metadata": {
                "team": categories.get("team", ""),
                "commitment": categories.get("commitment", ""),
            },
        }
