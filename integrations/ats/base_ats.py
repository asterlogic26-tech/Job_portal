from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseATSClient(ABC):
    """Abstract ATS integration client."""

    @abstractmethod
    async def get_jobs(self, company_slug: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch available jobs from ATS."""
        ...

    @abstractmethod
    async def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed job info."""
        ...
