"""
Shared pytest fixtures and configuration.
No database is spun up here — all DB interactions are mocked.
"""
import os
import pytest

# Provide minimal env vars so backend.core.config can load without real services
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
