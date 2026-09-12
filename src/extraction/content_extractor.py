from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from src.extraction.html_cleaner import clean_html, extract_evidence_snippet
from src.extraction.metadata import extract_metadata_from_html
from src.extraction.date_parser import parse_publication_date, format_iso_utc

class ContentExtractor:
    """Combines metadata extraction, HTML cleaning, and date resolution."""

    @staticmethod
    def extract(html: str, max_chars: int = 12000) -> Dict[str, Any]:
        """Extracts cleaned text, metadata, and publication timestamp."""
        metadata = extract_metadata_from_html(html)
        clean_text = clean_html(html, max_chars=max_chars)

        # Look for JSON-LD date
        json_ld_date = None
        for item in metadata.get("json_ld", []):
            if isinstance(item, dict):
                json_ld_date = item.get("datePublished") or item.get("uploadDate")
                if json_ld_date:
                    break

        resolved_date = parse_publication_date(
            json_ld_date=json_ld_date,
            og_date=metadata.get("og_published_time"),
            time_tag=metadata.get("time_tag"),
            raw_date=None
        )

        iso_date = format_iso_utc(resolved_date) if resolved_date else None

        return {
            "title": metadata.get("og_title") or metadata.get("title") or "",
            "text": clean_text,
            "published_date": iso_date,
            "metadata": metadata
        }
