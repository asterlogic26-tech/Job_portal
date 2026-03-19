"""Unit tests for engines.matching.salary_scorer"""
import pytest
from engines.matching.salary_scorer import compute_salary_score


class TestComputeSalaryScore:
    def test_all_unknown_returns_neutral(self):
        score = compute_salary_score(None, None, None, None)
        assert score == pytest.approx(0.5)

    def test_partial_info_returns_neutral(self):
        # job has range but profile doesn't
        score = compute_salary_score(100_000, 150_000, None, None)
        assert score == pytest.approx(0.5)

    def test_perfect_overlap(self):
        # Identical ranges → full overlap
        score = compute_salary_score(100_000, 150_000, 100_000, 150_000)
        assert score >= 0.9

    def test_no_overlap_profile_wants_more(self):
        # Profile: 200k–250k; Job: 80k–100k
        score = compute_salary_score(80_000, 100_000, 200_000, 250_000)
        assert score < 0.5

    def test_job_pays_more_is_good(self):
        # Job: 200k–300k; Profile: 80k–100k → positive for user
        score = compute_salary_score(200_000, 300_000, 80_000, 100_000)
        assert score == pytest.approx(0.8)

    def test_partial_overlap_between_zero_and_one(self):
        score = compute_salary_score(100_000, 150_000, 130_000, 180_000)
        assert 0.0 < score <= 1.0

    def test_score_bounded(self):
        cases = [
            (50_000, 80_000, 120_000, 160_000),
            (150_000, 200_000, 100_000, 130_000),
            (100_000, 120_000, 100_000, 120_000),
        ]
        for args in cases:
            score = compute_salary_score(*args)
            assert 0.0 <= score <= 1.0
