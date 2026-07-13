"""Calculation freshness validation."""

from datetime import datetime, timedelta, timezone

from app.live.exceptions import LiveValidationException
from app.live.models.analytics import LiveAnalyticsSnapshot


class FreshnessValidator:
    """Validate analytics timestamp ordering and freshness."""

    def __init__(self, *, max_age_seconds: int = 30) -> None:
        self._max_age = max_age_seconds
        self._last_seen: datetime | None = None

    def validate(self, snapshot: LiveAnalyticsSnapshot) -> None:
        ts = snapshot.calculation_timestamp
        if ts is None:
            raise LiveValidationException("Analytics timestamp is required")
        if self._last_seen is not None and ts < self._last_seen:
            raise LiveValidationException("Analytics timestamp out of order")
        age = datetime.now(timezone.utc) - ts
        if age > timedelta(seconds=self._max_age):
            raise LiveValidationException("Analytics snapshot is stale")
        self._last_seen = ts
