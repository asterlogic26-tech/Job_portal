"""Unit tests for engines.matching.recency_scorer"""
import pytest
from datetime import datetime, timedelta, timezone
from engines.matching.recency_scorer import compute_recency_score


class TestComputeRecencyScore:
    def test_none_returns_neutral(self):
        assert compute_recency_score(None) == pytest.approx(0.5)

    def test_just_posted_near_one(self):
        now = datetime.now(timezone.utc)
        score = compute_recency_score(now)
        assert score >= 0.99

    def test_future_date_returns_one(self):
        future = datetime.now(timezone.utc) + timedelta(days=5)
        assert compute_recency_score(future) == pytest.approx(1.0)

    def test_half_life_at_14_days(self):
        two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
        score = compute_recency_score(two_weeks_ago, half_life_days=14)
        assert score == pytest.approx(0.5, abs=0.01)

    def test_old_posting_near_zero(self):
        ancient = datetime.now(timezone.utc) - timedelta(days=365)
        score = compute_recency_score(ancient)
        assert score < 0.01

    def test_score_bounded(self):
        for days_ago in [0, 1, 7, 14, 30, 90, 365]:
            dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
            score = compute_recency_score(dt)
            assert 0.0 <= score <= 1.0

    def test_naive_datetime_handled(self):
        # Naive datetime should not raise
        naive = datetime.utcnow() - timedelta(days=7)
        score = compute_recency_score(naive)
        assert 0.0 <= score <= 1.0

    def test_decay_is_monotonic(self):
        scores = []
        for days in [0, 7, 14, 30, 60]:
            dt = datetime.now(timezone.utc) - timedelta(days=days)
            scores.append(compute_recency_score(dt))
        assert scores == sorted(scores, reverse=True)
