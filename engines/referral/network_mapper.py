import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class NetworkMapper:
    """Maps user's network connections to target companies."""

    def find_connections_at_company(
        self,
        connections: List[Dict],
        company_name: str,
    ) -> List[Dict]:
        """Find connections who work at the target company."""
        company_lower = company_name.lower()
        matches = []

        for connection in connections:
            conn_company = connection.get("company", "").lower()
            if company_lower in conn_company or conn_company in company_lower:
                matches.append(connection)

        return sorted(matches, key=lambda c: c.get("tenure_months", 0), reverse=True)

    def score_connection(self, connection: Dict) -> float:
        """Score a connection's referral value."""
        score = 0.5

        tenure = connection.get("tenure_months", 0)
        if tenure >= 24:
            score += 0.3
        elif tenure >= 12:
            score += 0.2

        strength = connection.get("relationship_strength", "weak")
        if strength == "strong":
            score += 0.2
        elif strength == "medium":
            score += 0.1

        return min(score, 1.0)

    def get_referral_paths(
        self,
        connections: List[Dict],
        company_name: str,
    ) -> List[Dict]:
        """Get ranked referral opportunities for a company."""
        direct = self.find_connections_at_company(connections, company_name)
        paths = []
        for conn in direct:
            paths.append({
                "connection": conn,
                "path_length": 1,
                "score": self.score_connection(conn),
                "recommendation": "Strong referral opportunity" if self.score_connection(conn) > 0.7 else "Potential referral",
            })
        return sorted(paths, key=lambda p: p["score"], reverse=True)
