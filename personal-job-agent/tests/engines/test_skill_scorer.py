"""Unit tests for engines.matching.skill_scorer"""
import pytest
from engines.matching.skill_scorer import compute_skill_score


class TestComputeSkillScore:
    def test_perfect_match(self):
        score, details = compute_skill_score(
            ["Python", "FastAPI", "PostgreSQL"],
            ["python", "fastapi", "postgresql"],
        )
        assert score == pytest.approx(1.0)
        assert details["missing"] == []

    def test_no_match(self):
        score, details = compute_skill_score(
            ["Rust", "WASM"],
            ["Python", "Django"],
        )
        assert score == pytest.approx(0.0)
        assert len(details["missing"]) == 2

    def test_partial_match(self):
        score, details = compute_skill_score(
            ["Python", "Go", "Rust"],
            ["python"],
        )
        assert score == pytest.approx(1 / 3)
        assert "go" in details["missing"] or "rust" in details["missing"]

    def test_empty_job_skills_returns_neutral(self):
        score, details = compute_skill_score([], ["Python", "Go"])
        assert score == pytest.approx(0.7)
        assert details["matched"] == []
        assert details["missing"] == []

    def test_case_insensitive(self):
        score, _ = compute_skill_score(["PYTHON", "FastAPI"], ["python", "fastapi"])
        assert score == pytest.approx(1.0)

    def test_missing_capped_at_10(self):
        job_skills = [f"skill_{i}" for i in range(20)]
        score, details = compute_skill_score(job_skills, [])
        assert len(details["missing"]) <= 10

    def test_extra_profile_skills_do_not_affect_score(self):
        """Score is based on job skill coverage, not profile bloat."""
        score1, _ = compute_skill_score(["Python"], ["Python"])
        score2, _ = compute_skill_score(["Python"], ["Python", "Go", "Rust", "Java"])
        assert score1 == score2 == pytest.approx(1.0)
