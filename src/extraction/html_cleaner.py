import re
from bs4 import BeautifulSoup

def clean_html(raw_html: str, max_chars: int = 12000) -> str:
    """
    Cleans raw HTML by stripping scripts, styles, navigation, headers, footers,
    and extraneous tags, then returns normalized plain text truncated to max_chars.
    This prevents HTTP 413 and excessive token consumption.
    """
    if not raw_html:
        return ""

    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Remove noisy non-content elements
        for tag in soup([
            "script", "style", "nav", "footer", "header", "aside",
            "noscript", "svg", "iframe", "button", "input", "form"
        ]):
            tag.decompose()

        # Remove elements with common noise class/id names
        for element in soup.find_all(attrs={"class": re.compile(r"cookie|banner|ad-|advertisement|sidebar|popup", re.I)}):
            element.decompose()

        # Extract textual content
        text = soup.get_text(separator=" ", strip=True)
        
        # Normalize multiple spaces and blank lines
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate to maximum input characters
        if len(text) > max_chars:
            text = text[:max_chars]

        return text
    except Exception:
        # Fallback regex-based cleaning if parser fails
        stripped = re.sub(r"<[^>]+>", " ", raw_html)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        return stripped[:max_chars]

def extract_evidence_snippet(text: str, match_term: str = "", max_chars: int = 500) -> str:
    """
    Extracts a bounded snippet around a key term, guaranteed <= max_chars (e.g. 500).
    Never stores entire pages.
    """
    if not text:
        return ""
    if not match_term or match_term.lower() not in text.lower():
        return text[:max_chars].strip()

    idx = text.lower().find(match_term.lower())
    half = max(10, (max_chars - len(match_term)) // 2)
    start = max(0, idx - half)
    end = min(len(text), start + max_chars)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
