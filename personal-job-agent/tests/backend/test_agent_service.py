"""
Unit tests for backend.services.agent_service.AgentService.

All DB access and orchestrator execution are mocked so these tests
run without a live database or API keys.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


FIXED_JOB_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
FIXED_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PIPELINE_RUN_ID = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _mock_job():
    j = MagicMock()
    j.id = FIXED_JOB_ID
    j.title = "Senior Engineer"
    j.company_name = "Acme Corp"
    j.company_id = uuid.uuid4()
    j.description = "Build great things."
    j.seniority_level = "senior"
    j.salary_min = 130_000
    j.salary_max = 170_000
    j.required_skills = [{"name": "python"}]
    j.preferred_skills = []
    j.url = "https://example.com/job"
    j.apply_url = "https://example.com/apply"
    j.posted_at = None
    j.source = "linkedin"
    return j


def _mock_profile():
    p = MagicMock()
    p.full_name = "Jane Doe"
    p.current_title = "Engineer"
    p.skills = [{"name": "python"}]
    p.experience_years = 6
    p.target_salary_min = 120_000
    p.target_salary_max = 160_000
    p.location = "Remote"
    p.remote_preference = "remote"
    p.linkedin_url = ""
    p.github_url = ""
    p.resume_url = None
    p.bio = ""
    p.target_titles = []
    return p


def _mock_company():
    c = MagicMock()
    c.hiring_score = 55.0
    return c


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def svc(mock_db):
    from backend.services.agent_service import AgentService
    return AgentService(mock_db)


# ── build_context ─────────────────────────────────────────────────────────────

class TestBuildContext:
    @pytest.mark.asyncio
    async def test_raises_if_job_not_found(self, svc, mock_db):
        mock_db.get.return_value = None  # job not found
        with pytest.raises(ValueError, match="not found"):
            await svc.build_context(FIXED_JOB_ID, FIXED_USER_ID)

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self, svc, mock_db):
        # Mock DB.get calls: first for Job, second for UserProfile, third for Company
        mock_db.get.side_effect = [_mock_job(), _mock_profile(), _mock_company()]
        # Mock execute for company signals, network count, network connections
        scalar_mock = MagicMock()
        scalar_mock.scalar_one.return_value = 0
        scalar_mock.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = scalar_mock

        ctx = await svc.build_context(FIXED_JOB_ID, FIXED_USER_ID)

        assert "job_id" in ctx
        assert "title" in ctx
        assert "profile" in ctx
        assert "company_hiring_score" in ctx

    @pytest.mark.asyncio
    async def test_profile_none_returns_empty_profile(self, svc, mock_db):
        mock_db.get.side_effect = [_mock_job(), None, _mock_company()]
        scalar_mock = MagicMock()
        scalar_mock.scalar_one.return_value = 0
        scalar_mock.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = scalar_mock

        ctx = await svc.build_context(FIXED_JOB_ID, FIXED_USER_ID)
        assert ctx["profile"] == {}


# ── run_pipeline ──────────────────────────────────────────────────────────────

class TestRunPipeline:
    @pytest.mark.asyncio
    async def test_calls_orchestrator_and_saves_logs(self, svc):
        fake_pipeline_result = {
            "pipeline_run_id": PIPELINE_RUN_ID,
            "job_id": str(FIXED_JOB_ID),
            "success": True,
            "agent_results": {"job_analysis": {"required_skills": ["python"]}},
            "agent_logs": [
                {
                    "agent_name": "job_analysis",
                    "version": "1.0.0",
                    "pipeline_run_id": PIPELINE_RUN_ID,
                    "input": {},
                    "output": {"required_skills": ["python"]},
                    "error": None,
                    "duration_ms": 50.0,
                    "success": True,
                }
            ],
        }

        with (
            patch.object(svc, "build_context", new=AsyncMock(return_value={})),
            patch(
                "backend.services.agent_service.AgentOrchestrator",
                autospec=True,
            ) as MockOrchestrator,
        ):
            instance = MockOrchestrator.return_value
            instance.run_pipeline = AsyncMock(return_value=fake_pipeline_result)

            result = await svc.run_pipeline(FIXED_JOB_ID, FIXED_USER_ID)

        assert result["pipeline_run_id"] == PIPELINE_RUN_ID
        assert result["success"] is True
        assert result["agent_logs_saved"] == 1


# ── run_single_agent ──────────────────────────────────────────────────────────

class TestRunSingleAgent:
    @pytest.mark.asyncio
    async def test_persists_log_entry(self, svc, mock_db):
        with patch(
            "backend.services.agent_service.AgentOrchestrator",
            autospec=True,
        ) as MockOrchestrator:
            instance = MockOrchestrator.return_value
            instance.run_single = AsyncMock(return_value={"match_score": 85.0})

            output = await svc.run_single_agent(
                agent_name="matching",
                input_data={"title": "Engineer"},
                job_id=FIXED_JOB_ID,
                user_id=FIXED_USER_ID,
            )

        assert output["match_score"] == 85.0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


# ── list_logs ─────────────────────────────────────────────────────────────────

class TestListLogs:
    @pytest.mark.asyncio
    async def test_returns_list_response_shape(self, svc, mock_db):
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        rows_result = MagicMock()
        rows_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [count_result, rows_result]

        response = await svc.list_logs()

        assert response.total == 0
        assert response.items == []
        assert response.page == 1


# ── _truncate helper ──────────────────────────────────────────────────────────

class TestTruncate:
    def test_small_dict_unchanged(self):
        from backend.services.agent_service import _truncate
        data = {"key": "value"}
        assert _truncate(data) == data

    def test_large_dict_is_truncated(self):
        from backend.services.agent_service import _truncate
        data = {"x": "a" * 5000}
        result = _truncate(data, max_chars=100)
        assert result.get("_truncated") is True

    def test_unserializable_returns_empty(self):
        from backend.services.agent_service import _truncate

        class Unserializable:
            pass

        result = _truncate(Unserializable())
        assert result == {}
