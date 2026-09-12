from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from typing import List, Optional
from bs4 import BeautifulSoup
from src.crawler.base import BaseCrawler
from src.llm.schemas import JobEntity, JobContent, EntityMappingLog
from src.extraction.date_parser import parse_publication_date, format_iso_utc
from src.freshness.tracker import FreshnessTracker
from src.entity_resolution.resolver import EntityResolver
from src.utils.logging import logger

class JobCrawler(BaseCrawler):
    """Crawler for AI jobs across 5 distinct job boards with strict 24h freshness verification."""

    def __init__(self, name: str = "AI Jobs Monitor", entity_resolver: Optional[EntityResolver] = None):
        super().__init__(name=name)
        self.resolver = entity_resolver or EntityResolver()
        self.mapping_logs: List[EntityMappingLog] = []

    async def crawl(self, limit: int = 100) -> List[JobEntity]:
        fresh_jobs: List[JobEntity] = []
        logger.info(f"[{self.name}] Starting 24h fresh AI jobs monitoring across 5 boards...")

        # 1. RemoteOK AI
        try:
            data = await self.http_client.fetch_json("https://remoteok.com/api?tag=ai")
            if isinstance(data, list):
                # First item in RemoteOK is legal disclaimer
                for item in data[1:]:
                    raw_date = item.get("date")
                    company = item.get("company", "").strip()
                    url = item.get("url", "").strip() or f"https://remoteok.com/remote-jobs/{item.get('id', '')}"
                    if not company or not raw_date:
                        continue

                    dt = parse_publication_date(raw_date=raw_date)
                    if not dt:
                        continue
                    is_fresh, _ = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                    if not is_fresh:
                        continue

                    canonical_company, m_log = self.resolver.resolve(company, source_url=url)
                    self.mapping_logs.append(m_log)

                    job = JobEntity(
                        schemaVersion="1.0",
                        recordType="JOB",
                        source_url=url,
                        source_name="RemoteOK",
                        content=JobContent(
                            company=canonical_company,
                            date=format_iso_utc(dt),
                            is_remote=True,
                            role_family="Engineering"
                        )
                    )
                    fresh_jobs.append(job)
        except Exception as e:
            logger.error(f"[{self.name}] Error querying RemoteOK: {e}")

        # 2. Jobicy AI
        try:
            data = await self.http_client.fetch_json("https://jobicy.com/api/v2/remote-jobs?count=50&tag=ai")
            jobs = data.get("jobs", [])
            for item in jobs:
                pub_date = item.get("pubDate")
                company = item.get("companyName", "").strip()
                url = item.get("url", "").strip()
                if not company or not pub_date:
                    continue

                dt = parse_publication_date(rss_pub_date=pub_date)
                if not dt:
                    continue
                is_fresh, _ = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                if not is_fresh:
                    continue

                canonical_company, m_log = self.resolver.resolve(company, source_url=url)
                self.mapping_logs.append(m_log)

                job = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_url=url,
                    source_name="Jobicy",
                    content=JobContent(
                        company=canonical_company,
                        date=format_iso_utc(dt),
                        is_remote=True,
                        role_family="Engineering"
                    )
                )
                fresh_jobs.append(job)
        except Exception as e:
            logger.error(f"[{self.name}] Error querying Jobicy: {e}")

        # 3. Remotive AI
        try:
            data = await self.http_client.fetch_json("https://remotive.com/api/remote-jobs?category=software-dev&search=AI")
            jobs = data.get("jobs", [])
            for item in jobs:
                pub_date = item.get("publication_date")
                company = item.get("company_name", "").strip()
                url = item.get("url", "").strip()
                if not company or not pub_date:
                    continue

                dt = parse_publication_date(raw_date=pub_date)
                if not dt:
                    continue
                is_fresh, _ = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                if not is_fresh:
                    continue

                canonical_company, m_log = self.resolver.resolve(company, source_url=url)
                self.mapping_logs.append(m_log)

                job = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_url=url,
                    source_name="Remotive",
                    content=JobContent(
                        company=canonical_company,
                        date=format_iso_utc(dt),
                        is_remote=True,
                        role_family="Engineering"
                    )
                )
                fresh_jobs.append(job)
        except Exception as e:
            logger.error(f"[{self.name}] Error querying Remotive: {e}")

        # 4. WeWorkRemotely RSS
        try:
            xml_text = await self.http_client.fetch_text("https://weworkremotely.com/categories/remote-programming-jobs.rss")
            root = ET.fromstring(xml_text)
            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")
                if title_el is None or link_el is None or pub_el is None:
                    continue

                title = title_el.text.strip()
                url = link_el.text.strip()
                pub_str = pub_el.text.strip()

                # Title is typically "Company Name: Job Title"
                company = title.split(":")[0].strip() if ":" in title else title[:30]

                dt = parse_publication_date(rss_pub_date=pub_str)
                if not dt:
                    continue
                is_fresh, _ = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                if not is_fresh:
                    continue

                canonical_company, m_log = self.resolver.resolve(company, source_url=url)
                self.mapping_logs.append(m_log)

                job = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_url=url,
                    source_name="WeWorkRemotely",
                    content=JobContent(
                        company=canonical_company,
                        date=format_iso_utc(dt),
                        is_remote=True,
                        role_family="Engineering"
                    )
                )
                fresh_jobs.append(job)
        except Exception as e:
            logger.error(f"[{self.name}] Error querying WeWorkRemotely: {e}")

        # 5. Arbeitnow AI
        try:
            data = await self.http_client.fetch_json("https://www.arbeitnow.com/api/job-board-api")
            jobs = data.get("data", [])
            for item in jobs:
                created_at = item.get("created_at")
                company = item.get("company_name", "").strip()
                url = item.get("url", "").strip()
                tags = item.get("tags", [])
                
                # Check for AI relevance
                title_lower = item.get("title", "").lower()
                is_ai = any("ai" in t.lower() or "machine learning" in t.lower() or "data" in t.lower() for t in tags) or "ai" in title_lower
                if not is_ai or not company or not created_at:
                    continue

                # created_at is unix epoch or ISO
                if isinstance(created_at, (int, float)):
                    dt = datetime.fromtimestamp(created_at, tz=timezone.utc)
                else:
                    dt = parse_publication_date(raw_date=str(created_at))

                if not dt:
                    continue
                is_fresh, _ = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                if not is_fresh:
                    continue

                canonical_company, m_log = self.resolver.resolve(company, source_url=url)
                self.mapping_logs.append(m_log)

                job = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_url=url,
                    source_name="Arbeitnow",
                    content=JobContent(
                        company=canonical_company,
                        date=format_iso_utc(dt),
                        is_remote=item.get("remote", True),
                        role_family="Engineering"
                    )
                )
                fresh_jobs.append(job)
        except Exception as e:
            logger.error(f"[{self.name}] Error querying Arbeitnow: {e}")

        logger.info(f"[{self.name}] Ingestion complete: found {len(fresh_jobs)} verified <= 24h fresh jobs.")
        return fresh_jobs
