"""Market history manager."""

from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock

from app.market_data.models import HistoricalBar, HistoryPeriod, Quote


class HistoryManager:
    """Maintain intraday and historical market data."""

    def __init__(self) -> None:
        """Initialize history stores."""
        self._lock = RLock()
        self._intraday: dict[str, list[HistoricalBar]] = defaultdict(list)
        self._daily: dict[str, list[HistoricalBar]] = defaultdict(list)
        self._quote_history: dict[str, list[Quote]] = defaultdict(list)

    def add_bars(self, period: HistoryPeriod, key: str, bars: list[HistoricalBar]) -> None:
        """Add historical bars for a period."""
        with self._lock:
            store = self._intraday if period == HistoryPeriod.INTRADAY else self._daily
            store[key].extend(bars)

    def add_quote(self, key: str, quote: Quote) -> None:
        """Track quote history."""
        with self._lock:
            self._quote_history[key].append(quote)
            if len(self._quote_history[key]) > 5_000:
                self._quote_history[key] = self._quote_history[key][-5_000:]

    def get_bars(self, period: HistoryPeriod, key: str) -> list[HistoricalBar]:
        """Return bars for a period."""
        with self._lock:
            store = self._intraday if period == HistoryPeriod.INTRADAY else self._daily
            return list(store.get(key, []))

    def get_latest_quote(self, key: str) -> Quote | None:
        """Return latest quote from history."""
        with self._lock:
            history = self._quote_history.get(key, [])
            return history[-1] if history else None

    def latest_timestamp(self, key: str) -> datetime | None:
        """Return latest quote timestamp."""
        quote = self.get_latest_quote(key)
        return quote.timestamp if quote else None
