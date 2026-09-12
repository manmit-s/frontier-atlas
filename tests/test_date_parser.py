from datetime import datetime, timezone, timedelta
import pytest
from src.extraction.date_parser import (
    parse_iso_or_standard,
    parse_relative_time,
    parse_publication_date,
    format_iso_utc
)

def test_parse_iso_standard():
    dt = parse_iso_or_standard("2026-09-12T14:30:00Z")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 9
    assert dt.day == 12
    assert dt.tzinfo == timezone.utc

def test_parse_rfc_2822():
    # Common RSS format
    dt = parse_iso_or_standard("Sat, 12 Sep 2026 12:00:00 GMT")
    assert dt is not None
    assert dt.year == 2026
    assert dt.hour == 12

def test_parse_relative_time():
    ref = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    
    # 2 hours ago
    dt2 = parse_relative_time("2 hours ago", reference_time=ref)
    assert dt2 is not None
    assert dt2 == ref - timedelta(hours=2)

    # 45 minutes ago
    dt_min = parse_relative_time("45 mins ago", reference_time=ref)
    assert dt_min is not None
    assert dt_min == ref - timedelta(minutes=45)

    # Yesterday
    dt_yest = parse_relative_time("yesterday", reference_time=ref)
    assert dt_yest is not None
    assert dt_yest == ref - timedelta(days=1)

def test_publication_date_priority():
    # RSS pubDate should take priority over generic raw_date
    rss_date = "2026-09-12T10:00:00Z"
    raw_date = "2026-09-10T05:00:00Z"
    res = parse_publication_date(rss_pub_date=rss_date, raw_date=raw_date)
    assert res is not None
    assert res.hour == 10

def test_format_iso_utc():
    dt = datetime(2026, 9, 12, 8, 15, 0, tzinfo=timezone.utc)
    formatted = format_iso_utc(dt)
    assert formatted == "2026-09-12T08:15:00Z"
