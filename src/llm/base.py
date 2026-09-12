from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

class LLMRateLimitError(Exception):
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after

class LLMPayloadTooLargeError(Exception):
    pass

class LLMProviderError(Exception):
    pass

class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers (Gemini, Groq, DeepSeek)."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    async def extract_structured(
        self,
        prompt: str,
        content: str,
        schema: Type[BaseModel]
    ) -> BaseModel:
        """Extracts structured data adhering to a Pydantic schema."""
        pass
