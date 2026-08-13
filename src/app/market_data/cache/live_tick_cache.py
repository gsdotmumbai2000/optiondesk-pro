"""Thread-safe last-tick cache with LRU and expiration."""

from datetime import datetime, timezone
from threading import RLock

from app.logging.logging_manager import get_logger
from app.market_data.cache.keys import quote_key
from app.market_data.cache.lru import LruTtlCache
from app.market_data.diagnostics import is_index_related_text
from app.market_data.models.tick import TickSnapshot

logger = get_logger(__name__)


class LiveTickCache:
    """Maintain last tick per instrument with LRU eviction."""

    def __init__(self, *, max_entries: int = 10_000, ttl_seconds: int = 300) -> None:
        """Initialize tick cache."""
        self._store = LruTtlCache[TickSnapshot](max_entries, ttl_seconds)
        self._lock = RLock()
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
        # TEMPORARY DIAGNOSTIC (NIFTY spot-unavailable trace) - boundary 3:
        # live tick cache insertion, cash/index-related ticks only.
        is_index_cash = not tick.strike_price and is_index_related_text(tick.symbol)
        if is_index_cash:
            logger.debug(
                "[DIAG-3 CACHE-PRE] exchange={exchange!r} symbol={symbol!r} cache_key={cache_key!r} "
                "ltp={ltp!r} instrument_kind={instrument_kind!r}",
                exchange=tick.exchange,
                symbol=tick.symbol,
                cache_key=key,
                ltp=tick.ltp,
                instrument_kind="CASH_INDEX",
            )
        with self._lock:
            self._store.put(key, tick)
            self._last_update = tick.timestamp or datetime.now(timezone.utc)
        if is_index_cash:
            logger.debug(
                "[DIAG-3 CACHE-POST] cache_key={cache_key!r} stored={stored!r} "
                "validation_result={validation_result!r}",
                cache_key=key,
                stored=True,
                validation_result="ok" if tick.ltp is not None else "ltp_missing",
            )

    def get(self, exchange: str, symbol: str, **parts: str) -> TickSnapshot | None:
        """Return cached tick for an instrument."""
        key = quote_key(exchange, symbol, **parts)
        with self._lock:
            return self._store.get(key)

    def snapshot(self) -> dict[str, TickSnapshot]:
        """Return shallow copy of all cached ticks."""
        with self._lock:
            return {
                key: entry.value
                for key, entry in self._store._entries.items()  # noqa: SLF001
                if entry.value is not None
            }

    def count(self) -> int:
        """Return number of cached ticks."""
        return self._store.size()

    def purge_expired(self) -> int:
        """Purge expired tick entries."""
        return self._store.purge_expired()
