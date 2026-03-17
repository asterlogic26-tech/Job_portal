"""
Base agent class for all AI agents in the Personal Job Agent system.
"""
from __future__ import annotations

import abc
import logging
import time
from typing import Any, Dict


class BaseAgent(abc.ABC):
    """Abstract base for all AI agents.

    Subclasses must implement ``run(input_data)``.
    Use ``execute(input_data)`` to run with automatic timing, validation,
    error handling, and structured logging.
    """

    name: str = "base_agent"
    version: str = "1.0.0"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"agents.{self.name}")
        self._last_input: Dict[str, Any] = {}
        self._last_output: Dict[str, Any] = {}
        self._last_error: str | None = None
        self._duration_ms: float = 0.0
        self._success: bool = False

    @abc.abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's core logic.

        Args:
            input_data: Accumulated pipeline context dict.

        Returns:
            Structured output dict specific to this agent.
            Required keys are defined per agent in AGENT ARCHITECTURE spec.
        """
        ...

    def validate(self, input_data: Dict[str, Any]) -> bool:
        """Validate input_data before running.

        Override in subclasses to enforce required keys.
        Returns False → agent is skipped and logged as failed.
        """
        return isinstance(input_data, dict)

    def log_output(self) -> Dict[str, Any]:
        """Return a structured log entry for the last execution.

        Called by the orchestrator after each agent run to persist results.
        """
        return {
            "agent_name": self.name,
            "version": self.version,
            "input": self._last_input,
            "output": self._last_output,
            "error": self._last_error,
            "duration_ms": self._duration_ms,
            "success": self._success,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with timing, validation, and error handling.

        Always returns a dict — errors surface via the ``error`` key,
        not via exceptions, so the orchestrator can continue the pipeline.
        """
        self._last_input = input_data
        self._last_error = None
        self._success = False
        start = time.perf_counter()

        if not self.validate(input_data):
            self._last_error = f"Input validation failed for agent '{self.name}'"
            self._last_output = {"error": self._last_error}
            self._duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self.logger.warning(self._last_error)
            return self._last_output

        try:
            output = await self.run(input_data)
            self._last_output = output
            self._success = True
            self.logger.debug(
                "Agent '%s' completed in %.0f ms", self.name, self._duration_ms
            )
        except Exception as exc:
            self._last_error = f"{type(exc).__name__}: {exc}"
            self.logger.exception("Agent '%s' raised an exception", self.name)
            self._last_output = {"error": self._last_error}
        finally:
            self._duration_ms = round((time.perf_counter() - start) * 1000, 2)

        return self._last_output
