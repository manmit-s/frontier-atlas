import asyncio
from typing import Coroutine, Any, List

class ConcurrencyManager:
    """Manages bounded concurrent async task execution using an asyncio.Semaphore."""

    def __init__(self, max_concurrency: int = 15):
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Executes a coroutine within the bounded concurrency limit."""
        async with self._semaphore:
            return await coro

    async def gather_bounded(self, coros: List[Coroutine[Any, Any, Any]]) -> List[Any]:
        """Gathers multiple coroutines respecting concurrency limits."""
        tasks = [self.run(c) for c in coros]
        return await asyncio.gather(*tasks, return_exceptions=True)
