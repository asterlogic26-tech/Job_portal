from typing import Dict, List
from datetime import datetime, timezone


class ProfileHealthChecker:
    """Analyzes profile completeness and freshness."""

    def compute_health_score(self, profile) -> Dict:
        score = 0
        max_score = 100
        issues = []
        suggestions = []

        checks = [
            ("full_name", 10, "Add your full name"),
            ("current_title", 10, "Add your current job title"),
            ("summary", 15, "Write a professional summary"),
            ("linkedin_url", 10, "Add LinkedIn URL"),
            ("github_url", 5, "Add GitHub URL"),
            ("location", 10, "Add your location"),
        ]

        for field, points, suggestion in checks:
            value = getattr(profile, field, None)
            if value:
                score += points
            else:
                issues.append({"field": field, "message": f"Missing: {field}"})
                suggestions.append({"field": field, "action": suggestion, "impact": points})

        # Skills
        skills = profile.skills or []
        if len(skills) >= 10:
            score += 20
        elif len(skills) >= 5:
            score += 10
            suggestions.append({"field": "skills", "action": "Add more skills (aim for 10+)", "impact": 10})
        else:
            issues.append({"field": "skills", "message": "Too few skills listed"})
            suggestions.append({"field": "skills", "action": "Add at least 5 skills", "impact": 20})

        # Experience years
        if profile.experience_years and profile.experience_years > 0:
            score += 5

        # Salary range
        if profile.target_salary_min and profile.target_salary_max:
            score += 5

        # Target titles
        if profile.target_titles and len(profile.target_titles) > 0:
            score += 10

        grade = "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D"

        return {
            "score": score,
            "max_score": max_score,
            "grade": grade,
            "issues": issues,
            "suggestions": sorted(suggestions, key=lambda s: s["impact"], reverse=True),
        }
