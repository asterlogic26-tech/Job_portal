"""
Unit tests for the multi-agent system.

All LLM calls are mocked so tests run without API keys.
All DB operations are mocked so tests run without a database.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def _profile(**overrides):
    base = {
        "full_name": "Jane Doe",
        "current_title": "Senior Software Engineer",
        "skills": [
            {"name": "python"}, {"name": "fastapi"}, {"name": "postgresql"}
        ],
        "experience_years": 6,
        "target_salary_min": 120_000,
        "target_salary_max": 160_000,
        "bio": "",
        "linkedin_url": "",
        "github_url": "",
        "resume_url": None,
        "target_titles": [],
    }
    base.update(overrides)
    return base


def _job_context(**overrides):
    base = {
        "job_id": "aaaaaaaa-0000-0000-0000-000000000001",
        "title": "Senior Python Engineer",
        "company_name": "Acme Corp",
        "description": "We need a Python expert.",
        "seniority_level": "senior",
        "salary_min": 130_000,
        "salary_max": 170_000,
        "required_skills": ["python", "fastapi"],
        "preferred_skills": ["docker"],
        "url": "https://example.com/job",
        "apply_url": "https://example.com/apply",
        "posted_at": None,
        "company_hiring_score": 60.0,
        "company_signals": [],
        "network_connections_at_company": 1,
        "network_connections": [
            {
                "full_name": "Bob Smith",
                "current_company": "Acme Corp",
                "relationship_strength": 0.8,
                "can_refer": True,
            }
        ],
        "profile": _profile(),
    }
    base.update(overrides)
    return base


# ── BaseAgent ─────────────────────────────────────────────────────────────────

class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_execute_calls_run(self):
        from agents.base import BaseAgent

        class MyAgent(BaseAgent):
            name = "test"
            async def run(self, input_data):
                return {"result": 42}

        agent = MyAgent()
        out = await agent.execute({"x": 1})
        assert out == {"result": 42}
        assert agent._success is True

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self):
        from agents.base import BaseAgent

        class BrokenAgent(BaseAgent):
            name = "broken"
            async def run(self, input_data):
                raise RuntimeError("boom")

        agent = BrokenAgent()
        out = await agent.execute({})
        assert "error" in out
        assert agent._success is False

    @pytest.mark.asyncio
    async def test_log_output_structure(self):
        from agents.base import BaseAgent

        class SimpleAgent(BaseAgent):
            name = "simple"
            async def run(self, input_data):
                return {"done": True}

        agent = SimpleAgent()
        await agent.execute({"key": "val"})
        log = agent.log_output()
        assert "agent_name" in log
        assert "duration_ms" in log
        assert "success" in log
        assert log["success"] is True

    @pytest.mark.asyncio
    async def test_validate_rejects_non_dict(self):
        from agents.base import BaseAgent

        class AnyAgent(BaseAgent):
            name = "any"
            async def run(self, input_data):
                return {}

        agent = AnyAgent()
        out = await agent.execute("not a dict")  # type: ignore
        assert "error" in out


# ── MatchingAgent ─────────────────────────────────────────────────────────────

class TestMatchingAgent:
    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from agents.matching_agent import MatchingAgent
        agent = MatchingAgent()
        ctx = _job_context()
        out = await agent.execute(ctx)
        assert "match_score" in out
        assert "matched_skills" in out
        assert "missing_skills" in out

    @pytest.mark.asyncio
    async def test_score_between_0_and_100(self):
        from agents.matching_agent import MatchingAgent
        agent = MatchingAgent()
        out = await agent.execute(_job_context())
        assert 0 <= out["match_score"] <= 100

    @pytest.mark.asyncio
    async def test_no_profile_fails_validation(self):
        from agents.matching_agent import MatchingAgent
        agent = MatchingAgent()
        ctx = _job_context()
        del ctx["profile"]
        out = await agent.execute(ctx)
        assert "error" in out


# ── SuccessPredictorAgent ─────────────────────────────────────────────────────

class TestSuccessPredictorAgent:
    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from agents.success_predictor_agent import SuccessPredictorAgent
        agent = SuccessPredictorAgent()
        ctx = _job_context()
        ctx["matching"] = {"match_score": 75, "skill_coverage_pct": 80}
        out = await agent.execute(ctx)
        assert "success_score" in out
        assert "probability_label" in out

    @pytest.mark.asyncio
    async def test_probability_label_values(self):
        from agents.success_predictor_agent import SuccessPredictorAgent, _label
        assert _label(80) == "High"
        assert _label(50) == "Moderate"
        assert _label(20) == "Low"

    @pytest.mark.asyncio
    async def test_score_bounded(self):
        from agents.success_predictor_agent import SuccessPredictorAgent
        agent = SuccessPredictorAgent()
        ctx = _job_context()
        ctx["matching"] = {"match_score": 0, "skill_coverage_pct": 0}
        out = await agent.execute(ctx)
        assert 0 <= out["success_score"] <= 100


# ── ApplicationAgent ──────────────────────────────────────────────────────────

class TestApplicationAgent:
    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from agents.application_agent import ApplicationAgent
        agent = ApplicationAgent()
        ctx = _job_context()
        ctx["matching"] = {"match_score": 80, "matched_skills": ["python"], "missing_skills": []}
        out = await agent.execute(ctx)
        assert "application_steps" in out
        assert "form_data" in out
        assert "status" in out

    @pytest.mark.asyncio
    async def test_status_ready_on_high_match(self):
        from agents.application_agent import ApplicationAgent
        agent = ApplicationAgent()
        ctx = _job_context()
        ctx["matching"] = {"match_score": 90, "matched_skills": ["python"], "missing_skills": []}
        out = await agent.execute(ctx)
        assert out["status"] == "ready"

    @pytest.mark.asyncio
    async def test_status_consider_skipping_on_low_match(self):
        from agents.application_agent import ApplicationAgent
        agent = ApplicationAgent()
        ctx = _job_context()
        ctx["matching"] = {"match_score": 10, "matched_skills": [], "missing_skills": ["rust", "go"]}
        out = await agent.execute(ctx)
        assert out["status"] == "consider_skipping"

    @pytest.mark.asyncio
    async def test_steps_is_nonempty_list(self):
        from agents.application_agent import ApplicationAgent
        agent = ApplicationAgent()
        ctx = _job_context()
        ctx["matching"] = {"match_score": 60, "matched_skills": ["python"], "missing_skills": []}
        out = await agent.execute(ctx)
        assert isinstance(out["application_steps"], list)
        assert len(out["application_steps"]) > 0


# ── CompanyRadarAgent ─────────────────────────────────────────────────────────

class TestCompanyRadarAgent:
    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from agents.company_radar_agent import CompanyRadarAgent
        agent = CompanyRadarAgent()
        ctx = _job_context()
        out = await agent.execute(ctx)
        assert "hiring_probability" in out
        assert "insights" in out

    @pytest.mark.asyncio
    async def test_probability_bounded(self):
        from agents.company_radar_agent import CompanyRadarAgent
        agent = CompanyRadarAgent()
        for score in [0, 50, 100]:
            ctx = _job_context(company_hiring_score=score)
            out = await agent.execute(ctx)
            assert 0 <= out["hiring_probability"] <= 100

    @pytest.mark.asyncio
    async def test_signals_appear_in_insights(self):
        from agents.company_radar_agent import CompanyRadarAgent
        agent = CompanyRadarAgent()
        ctx = _job_context(
            company_signals=[
                {"signal_type": "funding", "title": "Raised $50M Series B", "headline": ""}
            ]
        )
        out = await agent.execute(ctx)
        assert any("funding" in i.lower() or "Raised" in i for i in out["insights"])


# ── Orchestrator ──────────────────────────────────────────────────────────────

class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_pipeline_returns_required_keys(self):
        from agents.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        with patch("agents._llm.call_llm", new=AsyncMock(return_value="")):
            result = await orchestrator.run_pipeline(_job_context())

        assert "pipeline_run_id" in result
        assert "agent_results" in result
        assert "agent_logs" in result
        assert isinstance(result["agent_results"], dict)

    @pytest.mark.asyncio
    async def test_pipeline_continues_on_agent_failure(self):
        """Pipeline must not abort if one agent raises an exception."""
        from agents.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        # Break the matching agent
        with patch.object(
            orchestrator._get_agent("matching").__class__,
            "run",
            new=AsyncMock(side_effect=RuntimeError("matching broke")),
        ), patch("agents._llm.call_llm", new=AsyncMock(return_value="")):
            # Pre-instantiate to allow patching
            _ = orchestrator._get_agent("matching")
            result = await orchestrator.run_pipeline(_job_context())

        # Other agents should still have run
        assert "agent_logs" in result
        assert len(result["agent_logs"]) == len(orchestrator.pipeline_sequence())

    @pytest.mark.asyncio
    async def test_run_single_unknown_agent_raises(self):
        from agents.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        with pytest.raises(ValueError, match="Unknown agent"):
            await orchestrator.run_single("nonexistent_agent", {})

    def test_available_agents_nonempty(self):
        from agents.orchestrator import AgentOrchestrator
        agents = AgentOrchestrator.available_agents()
        assert len(agents) > 0

    def test_pipeline_sequence_order(self):
        from agents.orchestrator import AgentOrchestrator
        seq = AgentOrchestrator.pipeline_sequence()
        assert seq[0] == "job_analysis"
        assert "matching" in seq
        assert "resume" in seq
