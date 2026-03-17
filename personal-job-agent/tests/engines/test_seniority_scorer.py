"""Unit tests for engines.matching.seniority_scorer"""
import pytest
from engines.matching.seniority_scorer import compute_seniority_score


class TestComputeSeniorityScore:
    def test_exact_fit_mid(self):
        # mid: 2-5 years
        assert compute_seniority_score("mid", 3) == pytest.approx(1.0)

    def test_exact_fit_senior(self):
        # senior: 5-10 years
        assert compute_seniority_score("senior", 7) == pytest.approx(1.0)

    def test_under_qualified_penalized(self):
        # junior: 0-2 years, user has 0 — at boundary
        score_fit = compute_seniority_score("senior", 5)
        score_under = compute_seniority_score("senior", 1)
        assert score_fit > score_under

    def test_over_qualified_at_least_half(self):
        # Over-qualified should still return >= 0.5
        score = compute_seniority_score("junior", 15)
        assert score >= 0.5

    def test_unknown_seniority_returns_neutral(self):
        assert compute_seniority_score(None, 5) == pytest.approx(0.7)

    def test_unknown_level_string_returns_default(self):
        # Unmapped seniority defaults to (2,5) range
        score = compute_seniority_score("wizard", 3)
        assert 0.0 <= score <= 1.0

    def test_score_bounded(self):
        for years in [0, 1, 3, 7, 15, 30]:
            score = compute_seniority_score("senior", years)
            assert 0.0 <= score <= 1.0

    def test_case_insensitive(self):
        score_lower = compute_seniority_score("senior", 7)
        score_upper = compute_seniority_score("Senior", 7)
        assert score_lower == score_upper
