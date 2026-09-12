import asyncio
import time
from typing import Any, Dict, Optional
import aiohttp
from src.config.settings import settings
from src.crawler.retry import parse_retry_after, calculate_backoff
from src.utils.logging import logger, log_task_metric

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
]

class HTTPRateLimitError(Exception):
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after

class HTTPClient:
    """High-performance async HTTP client with pooling, retry, backoff, and 429 handling."""

    def __init__(
        self,
        max_concurrency: int = settings.MAX_CONCURRENCY,
        timeout_seconds: int = settings.REQUEST_TIMEOUT
    ):
        self.max_concurrency = max_concurrency
        self.timeout = aiohttp.ClientTimeout(
            total=timeout_seconds,
            connect=10.0,
            sock_read=timeout_seconds
        )
        self._session: Optional[aiohttp.ClientSession] = None
        self._ua_index = 0

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrency,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        return self._session

    def _get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        ua = DEFAULT_USER_AGENTS[self._ua_index % len(DEFAULT_USER_AGENTS)]
        self._ua_index += 1
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    async def fetch_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = settings.CRAWLER_MAX_RETRIES
    ) -> str:
        """Fetches text/HTML with exponential backoff and jitter."""
        session = await self.get_session()
        req_headers = self._get_headers(headers)
        start_time = time.time()

        for attempt in range(max_retries + 1):
            try:
                async with session.get(url, params=params, headers=req_headers) as resp:
                    latency = (time.time() - start_time) * 1000

                    if resp.status == 200:
                        content = await resp.text(errors="replace")
                        log_task_metric("crawler", "GET", url, "200_OK", latency)
                        return content

                    if resp.status == 429:
                        retry_after_hdr = resp.headers.get("Retry-After")
                        retry_after = parse_retry_after(retry_after_hdr)
                        delay = retry_after if retry_after else calculate_backoff(attempt, settings.CRAWLER_BASE_BACKOFF, settings.CRAWLER_MAX_BACKOFF)
                        log_task_metric("crawler", "GET", url, "429_RATE_LIMIT", latency, f"backoff={delay:.1f}s")
                        if attempt == max_retries:
                            raise HTTPRateLimitError(f"HTTP 429 Too Many Requests for {url}", retry_after=retry_after)
                        await asyncio.sleep(delay)
                        continue

                    if resp.status in {500, 502, 503, 504}:
                        delay = calculate_backoff(attempt, settings.CRAWLER_BASE_BACKOFF, settings.CRAWLER_MAX_BACKOFF)
                        log_task_metric("crawler", "GET", url, f"HTTP_{resp.status}", latency, f"retry_in={delay:.1f}s")
                        if attempt == max_retries:
                            resp.raise_for_status()
                        await asyncio.sleep(delay)
                        continue

                    # Non-retryable error
                    log_task_metric("crawler", "GET", url, f"HTTP_{resp.status}", latency)
                    resp.raise_for_status()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                latency = (time.time() - start_time) * 1000
                if attempt == max_retries:
                    log_task_metric("crawler", "GET", url, "FAILED", latency, str(e))
                    raise e
                delay = calculate_backoff(attempt, settings.CRAWLER_BASE_BACKOFF, settings.CRAWLER_MAX_BACKOFF)
                log_task_metric("crawler", "GET", url, "RETRY", latency, f"err={type(e).__name__}, delay={delay:.1f}s")
                await asyncio.sleep(delay)

        raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")

    async def fetch_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """Fetches and parses JSON."""
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)
        text = await self.fetch_text(url, params=params, headers=req_headers)
        import json
        return json.loads(text)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
