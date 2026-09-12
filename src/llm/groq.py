import json
from typing import Any, Dict, Optional, Type
import aiohttp
from pydantic import BaseModel
from src.config.settings import settings
from src.llm.base import BaseLLMProvider, LLMRateLimitError, LLMPayloadTooLargeError, LLMProviderError
from src.crawler.retry import parse_retry_after

class GroqProvider(BaseLLMProvider):
    """Groq-hosted Llama 3 provider."""

    def __init__(
        self,
        model_name: str = settings.GROQ_MODEL,
        api_key: Optional[str] = settings.GROQ_API_KEY
    ):
        super().__init__(model_name=model_name, api_key=api_key)

    async def extract_structured(
        self,
        prompt: str,
        content: str,
        schema: Type[BaseModel]
    ) -> BaseModel:
        if not self.api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"
        system_msg = (
            "You are an AI data extraction engine. Output strictly JSON matching the required schema.\n"
            "Do NOT hallucinate. Use null for missing data.\n"
            f"Schema: {schema.model_json_schema()}"
        )
        user_msg = f"Task: {prompt}\n\nContent:\n{content}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": settings.MAX_OUTPUT_TOKENS
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    choice_text = data["choices"][0]["message"]["content"]
                    parsed = json.loads(choice_text)
                    return schema.model_validate(parsed)

                if resp.status == 429:
                    retry_after = parse_retry_after(resp.headers.get("Retry-After"))
                    raise LLMRateLimitError("Groq 429 Rate Limit", retry_after=retry_after)

                if resp.status == 413:
                    raise LLMPayloadTooLargeError("Groq 413 Payload Too Large")

                body = await resp.text()
                raise LLMProviderError(f"Groq API error {resp.status}: {body[:200]}")
