import asyncio
import pytest
from src.crawler.concurrency import ConcurrencyManager
from src.freshness.deduplication import Deduplicator
from src.utils.hashing import canonicalize_url, hash_url

def test_concurrency_manager_bounds():
    async def _runner():
        max_concurrent = 3
        manager = ConcurrencyManager(max_concurrency=max_concurrent)
        active_tasks = 0
        max_observed = 0

        async def worker():
            nonlocal active_tasks, max_observed
            active_tasks += 1
            max_observed = max(max_observed, active_tasks)
            await asyncio.sleep(0.05)
            active_tasks -= 1
            return True

        coros = [worker() for _ in range(10)]
        results = await manager.gather_bounded(coros)
        assert len(results) == 10
        assert all(r is True for r in results)
        assert max_observed <= max_concurrent

    asyncio.run(_runner())

def test_url_canonicalization():
    url1 = "HTTPS://WWW.Example.com:443/test/path/?utm_source=twitter&b=2&a=1#section"
    url2 = "https://www.example.com/test/path?a=1&b=2"
    assert canonicalize_url(url1) == canonicalize_url(url2)
    assert hash_url(url1) == hash_url(url2)

def test_deduplicator():
    dedup = Deduplicator()
    assert dedup.is_seen("OpenAI", scope="startup") is False
    assert dedup.is_seen("OpenAI", scope="startup") is True
    assert dedup.is_seen("Anthropic", scope="startup") is False
