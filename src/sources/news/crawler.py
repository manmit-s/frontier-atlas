import xml.etree.ElementTree as ET
from typing import List, Optional
from bs4 import BeautifulSoup
from src.crawler.base import BaseCrawler
from src.llm.schemas import NewsEntity, NewsContent, SourceInfo
from src.extraction.date_parser import parse_publication_date, format_iso_utc
from src.freshness.tracker import FreshnessTracker
from src.extraction.html_cleaner import clean_html
from src.utils.logging import logger

NEWS_SOURCES = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "Ars Technica AI", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Engadget AI", "url": "https://www.engadget.com/rss.xml"},
    {"name": "SiliconANGLE AI", "url": "https://siliconangle.com/feed/"}
]

class NewsCrawler(BaseCrawler):
    """Monitors 5 distinct AI news sources and extracts articles strictly <= 24 hours old."""

    def __init__(self, name: str = "AI News Monitor"):
        super().__init__(name=name)

    async def crawl(self, limit: int = 100) -> List[NewsEntity]:
        fresh_news: List[NewsEntity] = []
        logger.info(f"[{self.name}] Starting 24h fresh news ingestion across {len(NEWS_SOURCES)} feeds...")

        for source_cfg in NEWS_SOURCES:
            src_name = source_cfg["name"]
            feed_url = source_cfg["url"]

            try:
                raw_xml = await self.http_client.fetch_text(feed_url)
                # Parse RSS or Atom
                try:
                    root = ET.fromstring(raw_xml)
                except ET.ParseError:
                    # Fallback to BeautifulSoup XML parser if malformed
                    soup = BeautifulSoup(raw_xml, "xml")
                    items = soup.find_all(["item", "entry"])
                    for item in items:
                        title_tag = item.find(["title"])
                        link_tag = item.find(["link"])
                        pub_tag = item.find(["pubDate", "published", "updated", "dc:date"])
                        desc_tag = item.find(["description", "summary", "content"])

                        title = title_tag.text.strip() if title_tag else ""
                        article_url = link_tag.get("href") or (link_tag.text.strip() if link_tag else "")
                        pub_str = pub_tag.text.strip() if pub_tag else ""
                        desc_clean = clean_html(desc_tag.text, max_chars=400) if desc_tag else ""

                        if not title or not article_url:
                            continue

                        dt = parse_publication_date(rss_pub_date=pub_str)
                        if not dt:
                            continue

                        is_fresh, reason = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                        if not is_fresh:
                            continue

                        news_entity = NewsEntity(
                            schemaVersion="1.0",
                            recordType="NEWS",
                            source=SourceInfo(name=src_name, url=article_url),
                            content=NewsContent(
                                title=title,
                                published_date=format_iso_utc(dt),
                                summary=desc_clean
                            )
                        )
                        fresh_news.append(news_entity)
                    continue

                # Standard XML ElementTree handling
                items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for item in items:
                    title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                    link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                    pub_el = (
                        item.find("pubDate")
                        or item.find("{http://www.w3.org/2005/Atom}published")
                        or item.find("{http://www.w3.org/2005/Atom}updated")
                    )
                    desc_el = (
                        item.find("description")
                        or item.find("{http://www.w3.org/2005/Atom}summary")
                        or item.find("{http://www.w3.org/2005/Atom}content")
                    )

                    title = title_el.text.strip() if title_el is not None and title_el.text else ""
                    if link_el is not None:
                        article_url = link_el.attrib.get("href") or (link_el.text.strip() if link_el.text else "")
                    else:
                        article_url = ""

                    pub_str = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
                    desc_clean = clean_html(desc_el.text, max_chars=400) if desc_el is not None and desc_el.text else ""

                    if not title or not article_url or not pub_str:
                        continue

                    dt = parse_publication_date(rss_pub_date=pub_str)
                    if not dt:
                        continue

                    is_fresh, reason = FreshnessTracker.is_fresh(dt, max_age_hours=24)
                    if not is_fresh:
                        continue

                    news_entity = NewsEntity(
                        schemaVersion="1.0",
                        recordType="NEWS",
                        source=SourceInfo(name=src_name, url=article_url),
                        content=NewsContent(
                            title=title,
                            published_date=format_iso_utc(dt),
                            summary=desc_clean
                        )
                    )
                    fresh_news.append(news_entity)

            except Exception as e:
                logger.error(f"[{self.name}] Error reading feed from {src_name}: {e}")

        logger.info(f"[{self.name}] Ingestion complete: found {len(fresh_news)} verified <= 24h fresh news articles.")
        return fresh_news
