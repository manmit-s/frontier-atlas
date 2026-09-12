from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.crawler.http_client import HTTPClient
from src.crawler.concurrency import ConcurrencyManager
from src.utils.logging import logger

class BaseCrawler(ABC):
    """Abstract Base Class for all vertical-specific crawlers."""

    def __init__(
        self,
        name: str,
        http_client: Optional[HTTPClient] = None,
        concurrency_manager: Optional[ConcurrencyManager] = None
    ):
        self.name = name
        self.http_client = http_client or HTTPClient()
        self.concurrency = concurrency_manager or ConcurrencyManager()

    @abstractmethod
    async def crawl(self, limit: int = 1000) -> List[Any]:
        """Executes asynchronous extraction returning structured entity models."""
        pass

    async def close(self) -> None:
        """Cleans up active HTTP sessions."""
        await self.http_client.close()
