from typing import List, Optional
from src.crawler.base import BaseCrawler
from src.llm.schemas import StartupEntity, StartupContent, StartupContentData, SourceInfo, EntityMappingLog
from src.entity_resolution.resolver import EntityResolver
from src.utils.logging import logger

class StartupCrawler(BaseCrawler):
    """Crawler for AI startups using GitHub AI Organizations & Directories."""

    def __init__(self, name: str = "GitHub AI Organizations", entity_resolver: Optional[EntityResolver] = None):
        super().__init__(name=name)
        self.resolver = entity_resolver or EntityResolver()
        self.mapping_logs: List[EntityMappingLog] = []

    async def crawl(self, limit: int = 1000) -> List[StartupEntity]:
        startups: List[StartupEntity] = []
        page = 1
        per_page = 100
        logger.info(f"[{self.name}] Ingesting startups (target: {limit})...")

        while len(startups) < limit and page <= 20:
            url = f"https://api.github.com/search/users?q=type:org+ai&per_page={per_page}&page={page}"
            try:
                data = await self.http_client.fetch_json(url)
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    if len(startups) >= limit:
                        break

                    login = item.get("login", "").strip()
                    html_url = item.get("html_url", "").strip()
                    if not login or not html_url:
                        continue

                    # Canonicalize entity name
                    canonical_name, map_log = self.resolver.resolve(login, source_url=html_url)
                    self.mapping_logs.append(map_log)

                    startup = StartupEntity(
                        schemaVersion="1.0",
                        recordType="STARTUP",
                        source=SourceInfo(
                            name=self.name,
                            url=html_url
                        ),
                        content=StartupContent(
                            entityName=canonical_name,
                            data=StartupContentData(employeeCount=None)
                        )
                    )
                    startups.append(startup)

                page += 1

            except Exception as e:
                logger.error(f"[{self.name}] Error fetching page {page}: {e}")
                break

        logger.info(f"[{self.name}] Ingestion complete: collected {len(startups)} startups.")
        return startups
