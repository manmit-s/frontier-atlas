import json
import re
from typing import Any, Dict, Optional, Type
import aiohttp
from pydantic import BaseModel
from src.config.settings import settings
from src.llm.base import BaseLLMProvider, LLMRateLimitError, LLMPayloadTooLargeError, LLMProviderError
from src.crawler.retry import parse_retry_after
from src.utils.logging import logger

class GeminiProvider(BaseLLMProvider):
    """Google Gemini Flash Provider."""

    def __init__(
        self,
        model_name: str = settings.GEMINI_MODEL,
        api_key: Optional[str] = settings.GEMINI_API_KEY
    ):
        super().__init__(model_name=model_name, api_key=api_key)

    async def extract_structured(
        self,
        prompt: str,
        content: str,
        schema: Type[BaseModel]
    ) -> BaseModel:
        if not self.api_key:
            raise LLMProviderError("GEMINI_API_KEY is not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        system_instruction = (
            "You are an expert AI data extraction engine. Extract structured data from the provided text.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Output ONLY valid JSON conforming to the schema.\n"
            "2. NEVER invent, hallucinate, or assume missing fields. If a field is not found in the text, use null.\n"
            f"Schema JSON format: {schema.model_json_schema()}"
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": f"{system_instruction}\n\nTask: {prompt}\n\nSource Content:\n{content}"}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0,
                "maxOutputTokens": settings.MAX_OUTPUT_TOKENS
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise LLMProviderError("Empty candidates returned by Gemini")
                    text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed_json = json.loads(text_out)
                    return schema.model_validate(parsed_json)

                if resp.status == 429:
                    retry_after = parse_retry_after(resp.headers.get("Retry-After"))
                    raise LLMRateLimitError("Gemini 429 Too Many Requests", retry_after=retry_after)

                if resp.status == 413:
                    raise LLMPayloadTooLargeError("Gemini 413 Payload Too Large")

                body = await resp.text()
                raise LLMProviderError(f"Gemini API error {resp.status}: {body[:200]}")
