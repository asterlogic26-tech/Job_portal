import os
import logging
from typing import Optional

from integrations.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)

_clients = {}


def get_llm_client(task_type: str = "primary") -> Optional[BaseLLMClient]:
    """
    Get LLM client based on task type.
    task_type: "primary" (quality-critical) or "cheap" (bulk/cheap tasks)
    """
    global _clients
    cache_key = task_type

    if cache_key in _clients:
        return _clients[cache_key]

    provider = os.environ.get("LLM_DEFAULT_PROVIDER", "anthropic")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    client = None

    if task_type == "primary":
        if provider == "anthropic" and anthropic_key:
            from integrations.llm.anthropic_client import AnthropicClient
            model = os.environ.get("LLM_PRIMARY_MODEL", "claude-haiku-4-5-20251001")
            client = AnthropicClient(api_key=anthropic_key, model=model)
        elif openai_key:
            from integrations.llm.openai_client import OpenAIClient
            client = OpenAIClient(api_key=openai_key, model="gpt-4o-mini")
    else:  # cheap
        if provider == "anthropic" and anthropic_key:
            from integrations.llm.anthropic_client import AnthropicClient
            model = os.environ.get("LLM_CHEAP_MODEL", "claude-haiku-4-5-20251001")
            client = AnthropicClient(api_key=anthropic_key, model=model)
        elif openai_key:
            from integrations.llm.openai_client import OpenAIClient
            model = os.environ.get("LLM_OPENAI_CHEAP_MODEL", "gpt-4o-mini")
            client = OpenAIClient(api_key=openai_key, model=model)

    if client:
        _clients[cache_key] = client
        logger.info(f"LLM client initialized: {type(client).__name__} ({client.model_name})")
    else:
        logger.warning("No LLM client available. Check API keys.")

    return client
