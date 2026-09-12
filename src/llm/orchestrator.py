import asyncio
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
from src.config.settings import settings
from src.llm.base import BaseLLMProvider, LLMRateLimitError, LLMPayloadTooLargeError, LLMProviderError
from src.llm.gemini import GeminiProvider
from src.llm.groq import GroqProvider
from src.llm.deepseek import DeepSeekProvider
from src.llm.chunker import reduce_payload
from src.crawler.retry import calculate_backoff
from src.utils.logging import logger

class LLMOrchestrator:
    """
    Multi-tier LLM Orchestration Engine.
    Executes fallback chain: Gemini Flash -> Groq Llama 3 -> DeepSeek.
    Handles 429 rate limits, 413 payload reductions, and offline deterministic fallback.
    """

    def __init__(self):
        self.providers: List[BaseLLMProvider] = [
            GeminiProvider(),
            GroqProvider(),
            DeepSeekProvider()
        ]
        self.telemetry = {
            "total_calls": 0,
            "gemini_calls": 0,
            "groq_fallbacks": 0,
            "deepseek_fallbacks": 0,
            "offline_fallbacks": 0,
            "rate_limit_429_count": 0,
            "payload_413_count": 0,
        }

    async def extract_with_fallback(
        self,
        prompt: str,
        content: str,
        schema: Type[BaseModel],
        max_retries_per_provider: int = settings.LLM_MAX_RETRIES
    ) -> BaseModel:
        """
        Runs the multi-tier fallback chain with 429 backoff and 413 payload truncation.
        """
        self.telemetry["total_calls"] += 1
        active_content = content

        for provider_idx, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__

            for attempt in range(max_retries_per_provider + 1):
                try:
                    result = await provider.extract_structured(prompt, active_content, schema)
                    if provider_idx == 0:
                        self.telemetry["gemini_calls"] += 1
                    elif provider_idx == 1:
                        self.telemetry["groq_fallbacks"] += 1
                    elif provider_idx == 2:
                        self.telemetry["deepseek_fallbacks"] += 1
                    return result

                except LLMPayloadTooLargeError:
                    self.telemetry["payload_413_count"] += 1
                    logger.warning(f"[{provider_name}] 413 Payload Too Large. Reducing content size by 50%...")
                    active_content = reduce_payload(active_content, reduction_factor=0.5)
                    if attempt == max_retries_per_provider:
                        logger.warning(f"[{provider_name}] Failed after reducing content. Falling back to next provider...")
                        break
                    continue

                except LLMRateLimitError as e:
                    self.telemetry["rate_limit_429_count"] += 1
                    if attempt == max_retries_per_provider:
                        logger.warning(f"[{provider_name}] Rate limit exhausted ({e}). Falling back to next provider...")
                        break
                    delay = e.retry_after if e.retry_after else calculate_backoff(attempt, settings.LLM_BASE_BACKOFF, settings.LLM_MAX_BACKOFF)
                    logger.warning(f"[{provider_name}] 429 Rate Limit. Backing off for {delay:.2f}s...")
                    await asyncio.sleep(delay)

                except (LLMProviderError, Exception) as e:
                    logger.info(f"[{provider_name}] Provider unavailable or returned error: {e}. Moving to next provider...")
                    break

        # If all cloud LLMs are unconfigured or exhausted: offline deterministic extraction
        self.telemetry["offline_fallbacks"] += 1
        logger.info("[LLMOrchestrator] Using deterministic rule-based extractor (offline mode).")
        return self._deterministic_extract(prompt, content, schema)

    def _deterministic_extract(self, prompt: str, content: str, schema: Type[BaseModel]) -> BaseModel:
        """Deterministic fallback that extracts without hallucinating."""
        schema_name = schema.__name__
        from src.llm.schemas import StartupEntity, ProductEntity, JobEntity, NewsEntity, PricingModelEnum

        # Simple deterministic rule parsing for common fields
        if schema_name == "StartupEntity":
            first_line = content.splitlines()[0] if content else "Unknown"
            name = first_line[:50].strip()
            return StartupEntity(
                source={"name": "Deterministic Extractor", "url": "local://extraction"},
                content={"entityName": name, "data": {"employeeCount": None}}
            )

        if schema_name == "ProductEntity":
            first_line = content.splitlines()[0] if content else "Unknown"
            return ProductEntity(
                source={"name": "Deterministic Extractor", "url": "local://extraction"},
                content={"startupName": first_line[:50].strip(), "pricingModel": PricingModelEnum.FREE}
            )

        # For generic schemas, instantiate default or null
        try:
            return schema.model_validate({})
        except Exception:
            raise RuntimeError(f"Unable to deterministically construct {schema_name}")
