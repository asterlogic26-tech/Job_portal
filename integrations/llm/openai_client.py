import json
import logging
import re
from typing import Optional

from integrations.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    async def complete(self, prompt: str, max_tokens: int = 500, system: Optional[str] = None) -> str:
        client = self._get_client()
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            def _call():
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content
            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def complete_json(self, prompt: str, max_tokens: int = 500) -> dict:
        response = await self.complete(prompt + "\nReturn ONLY valid JSON.", max_tokens=max_tokens)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
