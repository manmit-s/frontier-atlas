import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from src.database.database import get_db_connection
from src.llm.schemas import (
    StartupEntity,
    ProductEntity,
    ResearchPaperEntity,
    JobEntity,
    NewsEntity,
    EntityMappingLog
)
from src.utils.hashing import hash_url, hash_entity

class Repository:
    """Data Access Layer for normalized persistence with idempotency."""

    @staticmethod
    def is_url_processed(url: str) -> bool:
        """Checks if a URL has already been ingested."""
        url_h = hash_url(url)
        with get_db_connection() as conn:
            row = conn.execute("SELECT 1 FROM processed_urls WHERE url_hash = ?", (url_h,)).fetchone()
            return row is not None

    @staticmethod
    def mark_url_processed(url: str, source_name: str, processed_at: str) -> None:
        """Records a processed URL to prevent duplicate fetching."""
        url_h = hash_url(url)
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_urls (url_hash, url, source_name, processed_at) VALUES (?, ?, ?, ?)",
                (url_h, url, source_name, processed_at)
            )

    @staticmethod
    def insert_startups(startups: List[StartupEntity]) -> Tuple[int, int]:
        """Inserts startups, returning (inserted_count, duplicate_count)."""
        inserted = 0
        duplicates = 0
        with get_db_connection() as conn:
            for s in startups:
                # Key by canonical name + source URL
                hash_k = hash_entity(f"{s.content.entityName}:{s.source.url}", scope="startup")
                try:
                    conn.execute("""
                    INSERT INTO startups (
                        hash_key, schema_version, record_type, source_name, source_url,
                        entity_name, employee_count, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        hash_k,
                        s.schemaVersion,
                        s.recordType,
                        s.source.name,
                        s.source.url,
                        s.content.entityName,
                        s.content.data.employeeCount,
                        s.collectedAt
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    duplicates += 1
        return inserted, duplicates

    @staticmethod
    def insert_products(products: List[ProductEntity]) -> Tuple[int, int]:
        """Inserts products, returning (inserted_count, duplicate_count)."""
        inserted = 0
        duplicates = 0
        with get_db_connection() as conn:
            for p in products:
                hash_k = hash_entity(f"{p.content.startupName}:{p.source.url}", scope="product")
                try:
                    conn.execute("""
                    INSERT INTO products (
                        hash_key, schema_version, record_type, source_name, source_url,
                        startup_name, pricing_model, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        hash_k,
                        p.schemaVersion,
                        p.recordType,
                        p.source.name,
                        p.source.url,
                        p.content.startupName,
                        p.content.pricingModel.value,
                        p.collectedAt
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    duplicates += 1
        return inserted, duplicates

    @staticmethod
    def insert_research_papers(papers: List[ResearchPaperEntity]) -> Tuple[int, int]:
        """Inserts research papers, returning (inserted_count, duplicate_count)."""
        inserted = 0
        duplicates = 0
        with get_db_connection() as conn:
            for p in papers:
                hash_k = hash_entity(f"{p.content.title}:{p.content.paper_url}", scope="paper")
                authors_str = json.dumps(p.content.authors)
                try:
                    conn.execute("""
                    INSERT INTO research_papers (
                        hash_key, schema_version, record_type, title, authors,
                        paper_url, github_url, github_stars, published_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        hash_k,
                        p.schemaVersion,
                        p.recordType,
                        p.content.title,
                        authors_str,
                        p.content.paper_url,
                        p.content.github_url,
                        p.content.github_stars,
                        p.content.published_date,
                        p.collectedAt
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    duplicates += 1
        return inserted, duplicates

    @staticmethod
    def insert_jobs(jobs: List[JobEntity]) -> Tuple[int, int]:
        """Inserts fresh jobs, returning (inserted_count, duplicate_count)."""
        inserted = 0
        duplicates = 0
        with get_db_connection() as conn:
            for j in jobs:
                hash_k = hash_entity(f"{j.content.company}:{j.source_url}", scope="job")
                try:
                    conn.execute("""
                    INSERT INTO jobs (
                        hash_key, schema_version, record_type, source_name, source_url,
                        company, published_date, is_remote, role_family, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        hash_k,
                        j.schemaVersion,
                        j.recordType,
                        j.source_name,
                        j.source_url,
                        j.content.company,
                        j.content.date,
                        1 if j.content.is_remote else 0,
                        j.content.role_family,
                        j.collectedAt
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    duplicates += 1
        return inserted, duplicates

    @staticmethod
    def insert_news(news_list: List[NewsEntity]) -> Tuple[int, int]:
        """Inserts fresh news, returning (inserted_count, duplicate_count)."""
        inserted = 0
        duplicates = 0
        with get_db_connection() as conn:
            for n in news_list:
                hash_k = hash_entity(f"{n.content.title}:{n.source.url}", scope="news")
                try:
                    conn.execute("""
                    INSERT INTO news (
                        hash_key, schema_version, record_type, source_name, source_url,
                        title, published_date, summary, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        hash_k,
                        n.schemaVersion,
                        n.recordType,
                        n.source.name,
                        n.source.url,
                        n.content.title,
                        n.content.published_date,
                        n.content.summary,
                        n.collectedAt
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    duplicates += 1
        return inserted, duplicates

    @staticmethod
    def insert_entity_mappings(mappings: List[EntityMappingLog]) -> int:
        """Inserts entity mapping logs."""
        inserted = 0
        with get_db_connection() as conn:
            for m in mappings:
                conn.execute("""
                INSERT INTO entity_mappings (
                    raw_name, canonical_name, method, confidence, source_url, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    m.raw_name,
                    m.canonical_name,
                    m.method,
                    m.confidence,
                    m.source_url,
                    m.timestamp
                ))
                inserted += 1
        return inserted

    @staticmethod
    def get_counts() -> Dict[str, int]:
        """Retrieves total counts of all entities in database."""
        with get_db_connection() as conn:
            startups = conn.execute("SELECT COUNT(*) FROM startups").fetchone()[0]
            products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            papers = conn.execute("SELECT COUNT(*) FROM research_papers").fetchone()[0]
            jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            news = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
            mappings = conn.execute("SELECT COUNT(*) FROM entity_mappings").fetchone()[0]
            return {
                "startups": startups,
                "products": products,
                "research_papers": papers,
                "jobs": jobs,
                "news": news,
                "entity_mappings": mappings
            }

    @staticmethod
    def get_all_rows(table_name: str) -> List[Dict[str, Any]]:
        """Extracts all rows for a table as dictionaries (for exporting)."""
        valid_tables = {"startups", "products", "research_papers", "jobs", "news", "entity_mappings"}
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table: {table_name}")
        with get_db_connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            return [dict(row) for row in cursor.fetchall()]
