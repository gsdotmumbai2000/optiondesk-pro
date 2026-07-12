"""Thread-safe last-tick cache."""

from datetime import datetime, timezone
from threading import RLock

from app.market_data.cache.keys import quote_key
from app.market_data.models.tick import TickSnapshot


class TickCache:
    """Maintain last tick, OHLC, volume, and timestamps per instrument."""

    def __init__(self) -> None:
        """Initialize tick cache."""
        self._lock = RLock()
        self._ticks: dict[str, TickSnapshot] = {}
        self._last_update: datetime | None = None

    @property
    def last_update(self) -> datetime | None:
        """Return timestamp of the most recent tick."""
        with self._lock:
            return self._last_update

    def put(self, tick: TickSnapshot) -> None:
        """Store or replace a tick snapshot."""
        key = quote_key(
            tick.exchange,
            tick.symbol,
            expiry_date=tick.expiry_date,
            strike_price=tick.strike_price,
            option_right=tick.option_right,
        )
        with self._lock:
            self._ticks[key] = tick
            self._last_update = tick.timestamp or datetime.now(timezone.utc)

    def get(self, exchange: str, symbol: str, **parts: str) -> TickSnapshot | None:
        """Return cached tick for an instrument."""
        key = quote_key(exchange, symbol, **parts)
        with self._lock:
            return self._ticks.get(key)

    def count(self) -> int:
        """Return number of cached ticks."""
        with self._lock:
            return len(self._ticks)
