"""Pydantic schemas for the multi-agent system."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


# ── Agent Log ─────────────────────────────────────────────────────────────────

class AgentLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_name: str
    version: str
    pipeline_run_id: Optional[uuid.UUID]
    job_id: Optional[uuid.UUID]
    user_id: Optional[uuid.UUID]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    duration_ms: float
    success: bool
    created_at: datetime
    updated_at: datetime


class AgentLogListResponse(BaseModel):
    items: List[AgentLogRead]
    total: int
    page: int
    page_size: int


# ── Pipeline request / response ───────────────────────────────────────────────

class PipelineRunRequest(BaseModel):
    """Optional overrides when triggering a pipeline run."""
    include_agents: Optional[List[str]] = None   # if None → full pipeline
    additional_context: Optional[Dict[str, Any]] = None


class AgentRunRequest(BaseModel):
    """Run a single named agent with arbitrary input."""
    input_data: Dict[str, Any]


class AgentOutputRead(BaseModel):
    agent_name: str
    output: Dict[str, Any]
    duration_ms: float
    success: bool
    error: Optional[str] = None


class PipelineRunResponse(BaseModel):
    pipeline_run_id: str
    job_id: Optional[str]
    success: bool
    agent_results: Dict[str, Dict[str, Any]]
    agent_logs_saved: int


class SingleAgentResponse(BaseModel):
    agent_name: str
    output: Dict[str, Any]
    success: bool
    duration_ms: float
    error: Optional[str] = None
