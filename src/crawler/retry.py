import asyncio
import random
from typing import Callable, Any, Optional
from src.utils.logging import logger

def calculate_backoff(
    attempt: int,
    base: float = 1.0,
    max_backoff: float = 30.0,
    jitter: bool = True
) -> float:
    """Calculates exponential backoff with full jitter."""
    delay = min(max_backoff, base * (2 ** attempt))
    if jitter:
        delay = delay * random.uniform(0.5, 1.5)
    return max(0.1, delay)

def parse_retry_after(header_val: Optional[str]) -> Optional[float]:
    """Extracts seconds from HTTP Retry-After header."""
    if not header_val:
        return None
    try:
        val = float(header_val.strip())
        return max(0.0, val)
    except ValueError:
        return None

async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_backoff: float = 1.0,
    max_backoff: float = 30.0,
    retryable_exceptions: tuple = (Exception,),
    **kwargs: Any
) -> Any:
    """Executes an async function with exponential backoff and jitter."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_error = e
            if attempt == max_retries:
                logger.error(f"Exhausted {max_retries} retries for {func.__name__}: {e}")
                raise e
            
            # Check for retry-after attribute on exception if present
            retry_after = getattr(e, "retry_after", None)
            if retry_after is not None and isinstance(retry_after, (int, float)):
                delay = float(retry_after)
            else:
                delay = calculate_backoff(attempt, base_backoff, max_backoff)

            logger.warning(
                f"Retryable error in {func.__name__} (attempt {attempt + 1}/{max_retries}): {e}. "
                f"Backing off for {delay:.2f}s..."
            )
            await asyncio.sleep(delay)

    raise last_error or RuntimeError("Retry loop completed without result or exception")
