import json
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

def extract_metadata_from_html(html: str) -> Dict[str, Any]:
    """
    Extracts OpenGraph, JSON-LD, and standard HTML meta tags without running heavy models.
    """
    metadata: Dict[str, Any] = {
        "title": None,
        "description": None,
        "og_title": None,
        "og_description": None,
        "og_published_time": None,
        "json_ld": [],
        "time_tag": None
    }
    if not html:
        return metadata

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            metadata["title"] = title_tag.string.strip()

        # Meta tags
        for meta in soup.find_all("meta"):
            prop = meta.get("property", "").lower()
            name = meta.get("name", "").lower()
            content = meta.get("content", "")

            if not content:
                continue

            if prop == "og:title" or name == "og:title":
                metadata["og_title"] = content.strip()
            elif prop == "og:description" or name == "og:description":
                metadata["og_description"] = content.strip()
            elif prop in {"og:published_time", "article:published_time"} or name in {"og:published_time", "article:published_time"}:
                metadata["og_published_time"] = content.strip()
            elif name == "description":
                metadata["description"] = content.strip()

        # Time tags
        time_tag = soup.find("time")
        if time_tag:
            dt_attr = time_tag.get("datetime")
            metadata["time_tag"] = dt_attr.strip() if dt_attr else time_tag.get_text(strip=True)

        # JSON-LD scripts
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                try:
                    data = json.loads(script.string.strip())
                    metadata["json_ld"].append(data)
                except Exception:
                    pass

    except Exception:
        pass

    return metadata
