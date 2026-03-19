"""
Company Radar Agent

Analyses pre-collected company signals (funding rounds, news,
job velocity) to produce a hiring probability score and actionable
insights for the user.
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent


_SIGNAL_TYPE_LABELS = {
    "funding": "Recent funding round",
    "job_velocity": "Job posting momentum",
    "news": "Positive news coverage",
    "acquisition": "Acquisition / merger activity",
    "ipo": "IPO / public offering signal",
}


class CompanyRadarAgent(BaseAgent):
    """Evaluate company hiring probability from radar signals."""

    name = "company_radar"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        signals: List[Dict] = input_data.get("company_signals", [])
        company_hiring_score = float(input_data.get("company_hiring_score", 0))
        company_name = input_data.get("company_name", "this company")

        # Derive hiring probability (0–100) from the pre-computed hiring score
        hiring_probability = min(100.0, company_hiring_score)

        # Build human-readable insights from signals
        insights: List[str] = []
        for sig in signals[:5]:
            sig_type = sig.get("signal_type", "")
            label = _SIGNAL_TYPE_LABELS.get(sig_type, sig_type.replace("_", " ").title())
            title = sig.get("title") or sig.get("headline", "")
            if title:
                insights.append(f"{label}: {title}")

        # Add derived insight from the hiring score
        if company_hiring_score >= 70:
            insights.append(f"{company_name} is actively hiring — high job posting velocity")
        elif company_hiring_score >= 40:
            insights.append(f"{company_name} shows moderate hiring activity")
        else:
            insights.append(f"{company_name} has low recent hiring activity — consider timing")

        return {
            "hiring_probability": round(hiring_probability, 1),
            "insights": insights,
            "signal_count": len(signals),
            "raw_hiring_score": company_hiring_score,
        }
