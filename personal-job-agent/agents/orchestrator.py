"""
Agent Orchestrator

Coordinates the full multi-agent pipeline for a job application:

  job_data + profile
      → Job Analysis Agent
      → Matching Agent
      → Success Predictor Agent
      → Resume Agent
      → Application Agent
      → Recruiter Outreach Agent
      → Referral Agent

Each agent receives the accumulated context dict from all previous
agents and merges its output back into that context.

The orchestrator is stateless (no DB access).  The caller — either
``AgentService`` (async API) or the Celery task (sync wrapper) — is
responsible for loading data from the DB, passing it to
``run_pipeline()``, and persisting the returned logs.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from agents.job_analysis_agent import JobAnalysisAgent
from agents.matching_agent import MatchingAgent
from agents.success_predictor_agent import SuccessPredictorAgent
from agents.resume_agent import ResumeAgent
from agents.application_agent import ApplicationAgent
from agents.outreach_agent import OutreachAgent
from agents.referral_agent import ReferralAgent
from agents.company_radar_agent import CompanyRadarAgent
from agents.content_agent import ContentAgent

logger = logging.getLogger(__name__)

# Ordered pipeline sequence
_PIPELINE: List[str] = [
    "job_analysis",
    "matching",
    "success_predictor",
    "resume",
    "application",
    "outreach",
    "referral",
]

# All available agents (including standalone / on-demand ones)
_ALL_AGENTS = {
    "job_analysis": JobAnalysisAgent,
    "matching": MatchingAgent,
    "success_predictor": SuccessPredictorAgent,
    "resume": ResumeAgent,
    "application": ApplicationAgent,
    "outreach": OutreachAgent,
    "referral": ReferralAgent,
    "company_radar": CompanyRadarAgent,
    "content": ContentAgent,
}


class AgentOrchestrator:
    """Coordinate multiple AI agents for a single job pipeline run.

    Usage (async context)::

        orchestrator = AgentOrchestrator()
        result = await orchestrator.run_pipeline(context)

    The ``context`` dict must contain the job fields and ``profile`` sub-dict
    as built by ``AgentService.build_context()``.
    """

    def __init__(self) -> None:
        # Instantiate agents lazily so heavy models aren't loaded at import time
        self._instances: Dict[str, Any] = {}

    def _get_agent(self, name: str):
        if name not in self._instances:
            cls = _ALL_AGENTS.get(name)
            if cls is None:
                raise ValueError(f"Unknown agent: '{name}'")
            self._instances[name] = cls()
        return self._instances[name]

    async def run_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the full ordered pipeline.

        Args:
            context: Initial job + profile context dict.

        Returns:
            Dict containing:
              - ``pipeline_run_id``: unique run identifier (str UUID)
              - ``job_id``: forwarded from context
              - ``agent_results``: per-agent output dicts
              - ``agent_logs``: list of structured log entries
              - ``success``: True if at least one agent completed
        """
        run_id = str(uuid.uuid4())
        job_id = str(context.get("job_id", ""))

        results: Dict[str, Any] = {
            "pipeline_run_id": run_id,
            "job_id": job_id,
            "agent_results": {},
            "agent_logs": [],
            "success": False,
        }

        logger.info("Pipeline %s started for job %s", run_id, job_id)

        for agent_name in _PIPELINE:
            agent = self._get_agent(agent_name)
            output = await agent.execute(context)

            # Merge output into context for subsequent agents
            context[agent_name] = output

            log_entry = agent.log_output()
            log_entry["pipeline_run_id"] = run_id

            results["agent_results"][agent_name] = output
            results["agent_logs"].append(log_entry)

            if "error" in output and not output.get("success", True):
                logger.warning(
                    "Pipeline %s: agent '%s' failed — %s. Continuing.",
                    run_id, agent_name, output.get("error"),
                )
            else:
                results["success"] = True

        logger.info("Pipeline %s finished (success=%s)", run_id, results["success"])
        return results

    async def run_single(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a single named agent in isolation.

        Args:
            agent_name: Key from ``_ALL_AGENTS``.
            input_data: Context dict to pass directly to the agent.

        Returns:
            Agent output dict (may contain an ``error`` key on failure).

        Raises:
            ValueError: If ``agent_name`` is not registered.
        """
        agent = self._get_agent(agent_name)
        return await agent.execute(input_data)

    @staticmethod
    def available_agents() -> List[str]:
        """Return the list of all registered agent names."""
        return list(_ALL_AGENTS.keys())

    @staticmethod
    def pipeline_sequence() -> List[str]:
        """Return the default ordered pipeline sequence."""
        return list(_PIPELINE)
