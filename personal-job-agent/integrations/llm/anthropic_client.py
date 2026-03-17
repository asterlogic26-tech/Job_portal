import json
import logging
import re
from typing import Optional

from integrations.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model_name = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    async def complete(self, prompt: str, max_tokens: int = 500, system: Optional[str] = None) -> str:
        client = self._get_client()
        try:
            # Use sync client in async context via thread executor
            import asyncio
            loop = asyncio.get_event_loop()

            def _call():
                kwargs = {
                    "model": self.model_name,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system:
                    kwargs["system"] = system
                msg = client.messages.create(**kwargs)
                return msg.content[0].text

            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def complete_json(self, prompt: str, max_tokens: int = 500) -> dict:
        json_prompt = prompt + "\n\nReturn ONLY valid JSON, no explanation."
        response = await self.complete(json_prompt, max_tokens=max_tokens)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
