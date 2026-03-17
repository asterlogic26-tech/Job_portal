"""
Tests for engines.matching.matcher — the top-level compute_match_score function.

Sub-component scorers (skill, seniority, salary, recency) are tested
individually in their own test_*.py files.  Here we test the full
weighted aggregation and the derived output fields.
"""
import pytest
from unittest.mock import patch


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _job(**overrides):
    base = {
        "skills_required": [{"name": "python"}, {"name": "fastapi"}, {"name": "postgresql"}],
        "seniority_level": "senior",
        "salary_min": 120_000,
        "salary_max": 160_000,
        "posted_at": None,
    }
    base.update(overrides)
    return base


def _profile(**overrides):
    base = {
        "skills": [{"name": "python"}, {"name": "fastapi"}, {"name": "docker"}],
        "experience_years": 6,
        "target_salary_min": 120_000,
        "target_salary_max": 160_000,
    }
    base.update(overrides)
    return base


# ── Output shape ──────────────────────────────────────────────────────────────

class TestComputeMatchScoreShape:
    def test_returns_required_keys(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(_job(), _profile())
        required = {
            "match_score",
            "skill_coverage_pct",
            "skill_overlap_score",
            "seniority_fit_score",
            "salary_alignment_score",
            "recency_score",
            "risk_factors",
            "strength_factors",
            "scoring_breakdown",
        }
        assert required.issubset(result.keys())

    def test_score_between_0_and_100(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(_job(), _profile())
        assert 0 <= result["match_score"] <= 100

    def test_skill_coverage_pct_between_0_and_100(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(_job(), _profile())
        assert 0 <= result["skill_coverage_pct"] <= 100


# ── Score logic ───────────────────────────────────────────────────────────────

class TestComputeMatchScoreLogic:
    def test_perfect_skill_match_scores_higher(self):
        """Profile with all required skills scores higher than one with none."""
        from engines.matching.matcher import compute_match_score
        full_match = compute_match_score(
            _job(),
            _profile(skills=[{"name": "python"}, {"name": "fastapi"}, {"name": "postgresql"}]),
        )
        no_match = compute_match_score(
            _job(),
            _profile(skills=[{"name": "rust"}, {"name": "haskell"}]),
        )
        assert full_match["match_score"] > no_match["match_score"]

    def test_no_skills_job_does_not_crash(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(
            _job(skills_required=[]),
            _profile(skills=[]),
        )
        assert "match_score" in result

    def test_empty_profile_skills_returns_low_score(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(_job(), _profile(skills=[]))
        assert result["match_score"] < 50

    def test_company_hiring_score_boosts_result(self):
        from engines.matching.matcher import compute_match_score
        low = compute_match_score(_job(), _profile(), company_hiring_score=0)
        high = compute_match_score(_job(), _profile(), company_hiring_score=100)
        assert high["match_score"] >= low["match_score"]

    def test_risk_factors_on_low_skill_overlap(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(
            _job(skills_required=[{"name": "cobol"}, {"name": "fortran"}, {"name": "ada"}]),
            _profile(skills=[{"name": "python"}]),
        )
        assert len(result["risk_factors"]) > 0

    def test_strength_factors_on_high_skill_overlap(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(
            _job(skills_required=[{"name": "python"}, {"name": "fastapi"}]),
            _profile(skills=[{"name": "python"}, {"name": "fastapi"}, {"name": "postgresql"}]),
        )
        assert len(result["strength_factors"]) > 0

    def test_scoring_breakdown_has_correct_sub_keys(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(_job(), _profile())
        bd = result["scoring_breakdown"]
        assert "skill_overlap" in bd
        assert "matched_skills" in bd["skill_overlap"]
        assert "missing_skills" in bd["skill_overlap"]

    def test_matched_and_missing_skills_are_lists(self):
        from engines.matching.matcher import compute_match_score
        result = compute_match_score(_job(), _profile())
        bd = result["scoring_breakdown"]["skill_overlap"]
        assert isinstance(bd["matched_skills"], list)
        assert isinstance(bd["missing_skills"], list)


# ── Weight loading ────────────────────────────────────────────────────────────

class TestLoadWeights:
    def test_falls_back_to_defaults_when_file_missing(self):
        from engines.matching.matcher import load_weights, DEFAULT_WEIGHTS
        with patch("builtins.open", side_effect=FileNotFoundError):
            weights = load_weights()
        assert weights == DEFAULT_WEIGHTS

    def test_weights_sum_approximately_one(self):
        from engines.matching.matcher import DEFAULT_WEIGHTS
        total = sum(DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01
