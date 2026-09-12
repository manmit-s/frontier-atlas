import re
from typing import Dict, Optional, Tuple
import aiohttp
from src.config.settings import settings
from src.utils.logging import logger

GITHUB_REPO_REGEX = re.compile(r"github\.com/([^/]+)/([^/#?]+)", re.IGNORECASE)

class GitHubClient:
    """Async GitHub API client for repository metadata and live star counts."""

    def __init__(self, token: Optional[str] = settings.GITHUB_TOKEN):
        self.token = token
        self._stars_cache: Dict[str, int] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AIEngineerPipeline/1.0"}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            self._session = aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10))
        return self._session

    @staticmethod
    def extract_owner_repo(github_url: str) -> Optional[Tuple[str, str]]:
        """Extracts (owner, repo) from a GitHub repository URL."""
        if not github_url:
            return None
        match = GITHUB_REPO_REGEX.search(github_url)
        if match:
            owner = match.group(1).strip()
            repo = match.group(2).strip()
            if repo.endswith(".git"):
                repo = repo[:-4]
            return owner, repo
        return None

    async def get_repository_stars(self, github_url: str) -> Optional[int]:
        """Fetches live stargazers count from GitHub API with in-memory caching."""
        parsed = self.extract_owner_repo(github_url)
        if not parsed:
            return None

        owner, repo = parsed
        repo_key = f"{owner.lower()}/{repo.lower()}"

        if repo_key in self._stars_cache:
            return self._stars_cache[repo_key]

        session = await self.get_session()
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    stars = data.get("stargazers_count", 0)
                    self._stars_cache[repo_key] = stars
                    return stars
                elif resp.status in {403, 429}:
                    logger.warning(f"GitHub API rate limit encountered for {repo_key}.")
                    return None
                else:
                    return None
        except Exception as e:
            logger.debug(f"GitHub star fetch failed for {repo_key}: {e}")
            return None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
