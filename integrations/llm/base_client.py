from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """Abstract LLM client interface."""

    model_name: str = ""

    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 500, system: Optional[str] = None) -> str:
        """Generate a text completion."""
        ...

    @abstractmethod
    async def complete_json(self, prompt: str, max_tokens: int = 500) -> dict:
        """Generate a JSON completion."""
        ...
