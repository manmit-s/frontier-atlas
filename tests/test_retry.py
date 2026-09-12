import asyncio
import pytest
from src.crawler.retry import calculate_backoff, parse_retry_after, retry_async

def test_calculate_backoff_growth():
    b0 = calculate_backoff(attempt=0, base=1.0, max_backoff=30.0, jitter=False)
    b1 = calculate_backoff(attempt=1, base=1.0, max_backoff=30.0, jitter=False)
    b2 = calculate_backoff(attempt=2, base=1.0, max_backoff=30.0, jitter=False)
    assert b0 == 1.0
    assert b1 == 2.0
    assert b2 == 4.0

def test_calculate_backoff_max_bound():
    b10 = calculate_backoff(attempt=10, base=1.0, max_backoff=15.0, jitter=False)
    assert b10 == 15.0

def test_parse_retry_after():
    assert parse_retry_after("12") == 12.0
    assert parse_retry_after("2.5") == 2.5
    assert parse_retry_after(None) is None
    assert parse_retry_after("invalid") is None

def test_retry_async_eventual_success():
    calls = 0

    async def flaky_fn():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("Temporary glitch")
        return "success"

    result = asyncio.run(retry_async(flaky_fn, max_retries=3, base_backoff=0.01))
    assert result == "success"
    assert calls == 3
