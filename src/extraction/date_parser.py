import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from email.utils import parsedate_to_datetime
import dateutil.parser

RELATIVE_TIME_PATTERN = re.compile(
    r"(\d+)\s+(second|sec|minute|min|hour|hr|day|week|month|year)s?\s+ago",
    re.IGNORECASE
)

def parse_iso_or_standard(date_str: str) -> Optional[datetime]:
    """Attempts standard RFC / ISO / Dateutil parsing and returns timezone-aware UTC datetime."""
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    if not cleaned:
        return None

    # Try RFC 2822 (common in RSS/email)
    try:
        dt = parsedate_to_datetime(cleaned)
        if dt is not None:
            return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Try dateutil parser
    try:
        dt = dateutil.parser.parse(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        pass

    return None

def parse_relative_time(text: str, reference_time: Optional[datetime] = None) -> Optional[datetime]:
    """Parses expressions like '2 hours ago', '15 mins ago', 'yesterday'."""
    if not text or not isinstance(text, str):
        return None
    ref = reference_time or datetime.now(timezone.utc)
    text_lower = text.strip().lower()

    if "just now" in text_lower or "moments ago" in text_lower:
        return ref

    if "yesterday" in text_lower:
        return ref - timedelta(days=1)

    match = RELATIVE_TIME_PATTERN.search(text_lower)
    if match:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        if "sec" in unit:
            return ref - timedelta(seconds=amount)
        elif "min" in unit:
            return ref - timedelta(minutes=amount)
        elif "hour" in unit or "hr" in unit:
            return ref - timedelta(hours=amount)
        elif "day" in unit:
            return ref - timedelta(days=amount)
        elif "week" in unit:
            return ref - timedelta(weeks=amount)
        elif "month" in unit:
            return ref - timedelta(days=amount * 30)
        elif "year" in unit:
            return ref - timedelta(days=amount * 365)

    return None

def parse_publication_date(
    raw_date: Optional[str] = None,
    rss_pub_date: Optional[str] = None,
    json_ld_date: Optional[str] = None,
    og_date: Optional[str] = None,
    time_tag: Optional[str] = None,
    relative_str: Optional[str] = None,
    reference_time: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Deterministic date extraction following strict priority order:
    1. RSS/Atom pubDate
    2. JSON-LD datePublished
    3. OpenGraph published time
    4. <time datetime> tag
    5. Direct raw date string
    6. Relative date parsing
    Returns UTC timezone-aware datetime or None.
    """
    candidates = [
        rss_pub_date,
        json_ld_date,
        og_date,
        time_tag,
        raw_date
    ]

    for candidate in candidates:
        if candidate:
            dt = parse_iso_or_standard(candidate)
            if dt:
                return dt

    # Fallback to relative time
    for candidate in [relative_str, raw_date, time_tag]:
        if candidate:
            dt = parse_relative_time(candidate, reference_time=reference_time)
            if dt:
                return dt

    return None

def format_iso_utc(dt: datetime) -> str:
    """Formats a datetime object to standard ISO-8601 UTC string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
