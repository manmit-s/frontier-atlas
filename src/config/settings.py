from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    CONFIG_DIR: Path = BASE_DIR / "config"
    TEMP_DIR: Path = BASE_DIR / "data" / "temp"
    CACHE_DIR: Path = BASE_DIR / "data" / "cache"

    # LLM API Keys
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    # LLM Model Identifiers
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # LLM Request & Chunking Limits
    MAX_INPUT_CHARS: int = 12000
    MAX_CHUNK_CHARS: int = 4000
    MAX_OUTPUT_TOKENS: int = 1024
    LLM_MAX_RETRIES: int = 3
    LLM_BASE_BACKOFF: float = 1.5
    LLM_MAX_BACKOFF: float = 30.0

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    GOOGLE_SHEET_ID: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///data/intelligence.db"

    # Crawler Settings
    MAX_CONCURRENCY: int = 15
    REQUEST_TIMEOUT: int = 20
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_BASE_BACKOFF: float = 1.0
    CRAWLER_MAX_BACKOFF: float = 15.0

    # Disk & Storage Guards (Hard < 1 GB Constraint)
    MAX_PROJECT_FOOTPRINT_MB: float = 900.0
    MAX_TEMP_STORAGE_MB: float = 150.0
    MAX_SINGLE_TEMP_FILE_MB: float = 25.0

    # Entity Resolution
    FUZZY_CONFIDENCE_THRESHOLD: float = 88.0
    FUZZY_REVIEW_THRESHOLD: float = 75.0

settings = Settings()

# Ensure runtime directories exist
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
