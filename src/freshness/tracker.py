from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from src.extraction.date_parser import parse_iso_or_standard

class FreshnessTracker:
    """
    Validates that a publication timestamp falls strictly within the previous 24 hours.
    Allows a 15-minute clock drift margin for slight server desynchronization.
    """

    @staticmethod
    def is_fresh(
        dt_or_str: datetime | str,
        reference_time: Optional[datetime] = None,
        max_age_hours: int = 24
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates freshness.
        Returns: (is_fresh: bool, reason: Optional[str])
        """
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        if isinstance(dt_or_str, str):
            dt = parse_iso_or_standard(dt_or_str)
            if dt is None:
                return False, "UNPARSEABLE_DATE"
        elif isinstance(dt_or_str, datetime):
            dt = dt_or_str
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
        else:
            return False, "INVALID_DATE_TYPE"

        # Boundary checks
        earliest_allowed = now - timedelta(hours=max_age_hours)
        latest_allowed = now + timedelta(minutes=15) # 15-min clock drift tolerance

        if dt < earliest_allowed:
            age_hours = (now - dt).total_seconds() / 3600.0
            return False, f"STALE_RECORD (age: {age_hours:.1f}h > {max_age_hours}h)"

        if dt > latest_allowed:
            future_mins = (dt - now).total_seconds() / 60.0
            return False, f"FUTURE_TIMESTAMP (drift: +{future_mins:.1f}m)"

        return True, None
