"""Unit tests for backend.services.job_service — uses AsyncMock to avoid DB."""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.job_service import JobService
from backend.schemas.job import JobFilter


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def svc(mock_db):
    return JobService(mock_db)


def _make_job(**overrides):
    """Return a minimal Job-like object."""
    j = MagicMock()
    j.id = uuid.uuid4()
    j.title = overrides.get("title", "Software Engineer")
    j.company_name = overrides.get("company_name", "Acme Corp")
    j.location = overrides.get("location", "Remote")
    j.source = overrides.get("source", "linkedin")
    j.remote_policy = overrides.get("remote_policy", "remote")
    j.seniority_level = overrides.get("seniority_level", "senior")
    j.is_hidden = overrides.get("is_hidden", False)
    j.is_duplicate = overrides.get("is_duplicate", False)
    j.is_saved = overrides.get("is_saved", False)
    j.is_applied = overrides.get("is_applied", False)
    j.description = ""
    j.url = "https://example.com/job/1"
    j.apply_url = ""
    j.salary_min = None
    j.salary_max = None
    j.salary_currency = "USD"
    j.required_skills = []
    j.preferred_skills = []
    j.posted_at = None
    j.embedding_id = None
    j.content_hash = ""
    j.created_at = None
    j.updated_at = None
    j.match = None
    return j


class TestSetHidden:
    @pytest.mark.asyncio
    async def test_hides_job(self, svc, mock_db):
        job = _make_job()
        mock_db.get = AsyncMock(return_value=job)

        await svc.set_hidden(job.id, True)

        assert job.is_hidden is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_commit_when_job_missing(self, svc, mock_db):
        mock_db.get = AsyncMock(return_value=None)

        await svc.set_hidden(uuid.uuid4(), True)

        mock_db.commit.assert_not_called()


class TestSetSaved:
    @pytest.mark.asyncio
    async def test_saves_job(self, svc, mock_db):
        job = _make_job()
        mock_db.get = AsyncMock(return_value=job)

        await svc.set_saved(job.id, True)

        assert job.is_saved is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsaves_job(self, svc, mock_db):
        job = _make_job(is_saved=True)
        mock_db.get = AsyncMock(return_value=job)

        await svc.set_saved(job.id, False)

        assert job.is_saved is False
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_commit_when_job_missing(self, svc, mock_db):
        mock_db.get = AsyncMock(return_value=None)

        await svc.set_saved(uuid.uuid4(), True)

        mock_db.commit.assert_not_called()
