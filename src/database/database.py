import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from src.config.settings import settings
from src.utils.logging import logger

def get_db_path() -> Path:
    """Extracts local SQLite path from DATABASE_URL or defaults to data/intelligence.db"""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        rel_or_abs = url.replace("sqlite:///", "")
        path = Path(rel_or_abs)
        if not path.is_absolute():
            path = settings.BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    # Fallback to local default
    path = settings.DATA_DIR / "intelligence.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def init_db() -> None:
    """Initializes tables and compact pragmas in SQLite."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        # Compact performance pragmas
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA foreign_keys=ON;")

        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS startups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_key TEXT UNIQUE NOT NULL,
            schema_version TEXT NOT NULL,
            record_type TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            employee_count INTEGER,
            collected_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_key TEXT UNIQUE NOT NULL,
            schema_version TEXT NOT NULL,
            record_type TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            startup_name TEXT NOT NULL,
            pricing_model TEXT NOT NULL,
            collected_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_key TEXT UNIQUE NOT NULL,
            schema_version TEXT NOT NULL,
            record_type TEXT NOT NULL,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            paper_url TEXT NOT NULL,
            github_url TEXT,
            github_stars INTEGER,
            published_date TEXT NOT NULL,
            collected_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_key TEXT UNIQUE NOT NULL,
            schema_version TEXT NOT NULL,
            record_type TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            company TEXT NOT NULL,
            published_date TEXT NOT NULL,
            is_remote INTEGER NOT NULL,
            role_family TEXT NOT NULL,
            collected_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_key TEXT UNIQUE NOT NULL,
            schema_version TEXT NOT NULL,
            record_type TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            title TEXT NOT NULL,
            published_date TEXT NOT NULL,
            summary TEXT,
            collected_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            method TEXT NOT NULL,
            confidence REAL NOT NULL,
            source_url TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_urls (
            url_hash TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            source_name TEXT NOT NULL,
            processed_at TEXT NOT NULL
        );
        """)

        conn.commit()
    finally:
        conn.close()

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager providing a managed connection."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def vacuum_database() -> None:
    """Compacts the database to prevent fragment growth."""
    db_path = get_db_path()
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("VACUUM;")
            conn.commit()
        finally:
            conn.close()
