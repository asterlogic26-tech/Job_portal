import logging
import feedparser
import httpx
from typing import List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SignalCollector:
    """Collects company hiring signals from multiple sources."""

    async def collect_funding_signals(self, news_sources: List[Dict]) -> List[Dict]:
        """Parse funding news RSS feeds for company signals."""
        signals = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for source in news_sources:
                if not source.get("enabled"):
                    continue
                try:
                    resp = await client.get(source["url"])
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:20]:
                        if self._is_funding_news(entry.get("title", "")):
                            signals.append({
                                "source": source["id"],
                                "signal_type": "funding",
                                "headline": entry.get("title", ""),
                                "description": entry.get("summary", "")[:500],
                                "url": entry.get("link", ""),
                                "published_at": entry.get("published", ""),
                            })
                except Exception as e:
                    logger.error(f"Failed to fetch {source['url']}: {e}")
        return signals

    def _is_funding_news(self, title: str) -> bool:
        """Check if a news headline is about funding."""
        funding_keywords = [
            "raises", "funding", "series a", "series b", "series c",
            "seed round", "million", "billion", "valuation", "ipo",
            "acquires", "merger", "investment"
        ]
        title_lower = title.lower()
        return any(kw in title_lower for kw in funding_keywords)

    async def collect_job_velocity(self, company_id: str, job_count_30d: int, job_count_90d: int) -> Dict:
        """Compute job posting velocity signal."""
        if job_count_90d == 0:
            return {"signal_type": "job_velocity", "value": 0.0, "headline": "No historical data"}

        daily_30d = job_count_30d / 30
        daily_90d = job_count_90d / 90
        velocity = (daily_30d - daily_90d) / max(daily_90d, 0.1) * 100

        return {
            "signal_type": "job_velocity",
            "value": round(velocity, 1),
            "headline": f"Job posting velocity: {velocity:+.0f}% vs 90-day average",
        }

    def compute_hiring_score(self, signals: List[Dict], job_count_30d: int) -> float:
        """Compute composite hiring score from signals."""
        score = 0.0

        # Base from job posting volume
        score += min(job_count_30d * 2, 30)

        for signal in signals:
            if signal.get("signal_type") == "funding":
                score += 30
            elif signal.get("signal_type") == "job_velocity":
                velocity = signal.get("value", 0)
                if velocity > 50:
                    score += 20
                elif velocity > 20:
                    score += 10

        return round(min(score, 100), 1)
