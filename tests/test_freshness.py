from datetime import datetime, timezone, timedelta
import pytest
from src.freshness.tracker import FreshnessTracker

def test_freshness_within_24_hours():
    now = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    
    # 5 hours ago (Fresh)
    five_hours_ago = now - timedelta(hours=5)
    is_fresh, reason = FreshnessTracker.is_fresh(five_hours_ago, reference_time=now, max_age_hours=24)
    assert is_fresh is True
    assert reason is None

    # 23 hours ago (Fresh)
    twenty_three_ago = now - timedelta(hours=23)
    is_fresh, reason = FreshnessTracker.is_fresh(twenty_three_ago, reference_time=now, max_age_hours=24)
    assert is_fresh is True

def test_stale_record_rejected():
    now = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    
    # 25 hours ago (Stale - MUST REJECT)
    twenty_five_ago = now - timedelta(hours=25)
    is_fresh, reason = FreshnessTracker.is_fresh(twenty_five_ago, reference_time=now, max_age_hours=24)
    assert is_fresh is False
    assert "STALE_RECORD" in reason

    # 3 days ago
    three_days_ago = now - timedelta(days=3)
    is_fresh, reason = FreshnessTracker.is_fresh(three_days_ago, reference_time=now, max_age_hours=24)
    assert is_fresh is False

def test_future_drift_tolerance():
    now = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    
    # 5 mins in future (tolerated due to clock drift)
    slight_future = now + timedelta(minutes=5)
    is_fresh, reason = FreshnessTracker.is_fresh(slight_future, reference_time=now, max_age_hours=24)
    assert is_fresh is True

    # 2 hours in future (rejected)
    large_future = now + timedelta(hours=2)
    is_fresh, reason = FreshnessTracker.is_fresh(large_future, reference_time=now, max_age_hours=24)
    assert is_fresh is False
    assert "FUTURE_TIMESTAMP" in reason
