"""Calculation context cache."""

from datetime import datetime, timedelta, timezone
from threading import RLock

from app.calculation.context.calculation_context import CalculationContext


class ContextCache:
    """Thread-safe cache for latest calculation contexts."""

    def __init__(self, *, ttl_seconds: int = 300) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._lock = RLock()
        self._latest: dict[str, CalculationContext] = {}
        self._previous: dict[str, CalculationContext] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(self, key: str, context: CalculationContext) -> None:
        """Store context and rotate previous."""
        with self._lock:
            if key in self._latest:
                self._previous[key] = self._latest[key]
            self._latest[key] = context
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> CalculationContext | None:
        """Return latest context if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            return self._latest.get(key)

    def get_previous(self, key: str) -> CalculationContext | None:
        """Return previous context."""
        with self._lock:
            return self._previous.get(key)

    def compare(self, key: str) -> dict[str, object] | None:
        """Compare latest and previous contexts."""
        with self._lock:
            latest = self._latest.get(key)
            previous = self._previous.get(key)
            if latest is None or previous is None:
                return None
            return {
                "spot_price_changed": latest.spot_price != previous.spot_price,
                "volatility_changed": latest.volatility != previous.volatility,
                "days_to_expiry_changed": latest.days_to_expiry != previous.days_to_expiry,
            }

    def expire(self, key: str) -> None:
        """Expire a cached context."""
        with self._lock:
            self._latest.pop(key, None)
            self._previous.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.expire(key)
