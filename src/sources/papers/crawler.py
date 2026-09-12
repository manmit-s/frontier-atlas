from typing import List, Optional
from src.crawler.base import BaseCrawler
from src.github.client import GitHubClient
from src.llm.schemas import ResearchPaperEntity, ResearchPaperContent
from src.extraction.date_parser import parse_iso_or_standard, format_iso_utc
from src.utils.logging import logger

class ResearchPaperCrawler(BaseCrawler):
    """Crawler for AI research papers with GitHub correlation and live star counts."""

    def __init__(self, name: str = "Hugging Face Daily Papers & ArXiv", github_client: Optional[GitHubClient] = None):
        super().__init__(name=name)
        self.github_client = github_client or GitHubClient()

    async def crawl(self, limit: int = 1000) -> List[ResearchPaperEntity]:
        papers: List[ResearchPaperEntity] = []
        page = 0
        per_page = 100
        logger.info(f"[{self.name}] Ingesting research papers (target: {limit})...")

        while len(papers) < limit and page < 25:
            url = f"https://huggingface.co/api/daily_papers?limit={per_page}&p={page}"
            try:
                data = await self.http_client.fetch_json(url)
                if not isinstance(data, list) or not data:
                    break

                for item in data:
                    if len(papers) >= limit:
                        break

                    paper_obj = item.get("paper", {})
                    if not paper_obj:
                        continue

                    paper_id = paper_obj.get("id") or ""
                    title = paper_obj.get("title") or item.get("title") or "Untitled Paper"
                    raw_authors = paper_obj.get("authors", [])
                    authors = [a.get("name", "").strip() for a in raw_authors if isinstance(a, dict) and a.get("name")]
                    
                    published_at = paper_obj.get("publishedAt") or item.get("publishedAt") or ""
                    dt = parse_iso_or_standard(published_at)
                    iso_date = format_iso_utc(dt) if dt else published_at

                    paper_url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""
                    
                    # Extract GitHub repo correlation & star counts
                    gh_repo = paper_obj.get("githubRepo")
                    github_url = None
                    github_stars = paper_obj.get("githubStars")

                    if gh_repo:
                        if not gh_repo.startswith("http"):
                            github_url = f"https://github.com/{gh_repo}"
                        else:
                            github_url = gh_repo

                        if github_stars is None:
                            github_stars = await self.github_client.get_repository_stars(github_url)

                    paper_entity = ResearchPaperEntity(
                        schemaVersion="1.0",
                        recordType="RESEARCH_PAPER",
                        content=ResearchPaperContent(
                            title=title,
                            authors=authors,
                            paper_url=paper_url,
                            github_url=github_url,
                            github_stars=github_stars,
                            published_date=iso_date
                        )
                    )
                    papers.append(paper_entity)

                page += 1

            except Exception as e:
                logger.error(f"[{self.name}] Error fetching papers page {page}: {e}")
                break

        logger.info(f"[{self.name}] Ingestion complete: collected {len(papers)} research papers.")
        return papers
