"""Aggregates a live tick stream into fixed-interval OHLC candles.

MarketView feeds every incoming tick_updated payload through this; only the
OHLC bars, not raw ticks, are ever retained past their own interval, so
memory stays flat regardless of session length -- unlike buffering every
tick, which a full trading day of a liquid index would grow unbounded.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

_DEFAULT_INTERVAL = timedelta(minutes=1)
_DEFAULT_MAX_CANDLES = 120


@dataclass(frozen=True, slots=True)
class Candle:
    """One OHLC bar."""

    start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


class TickCandleBuffer:
    """Aggregate raw ticks into a bounded rolling window of OHLC candles."""

    def __init__(
        self,
        interval: timedelta = _DEFAULT_INTERVAL,
        max_candles: int = _DEFAULT_MAX_CANDLES,
    ) -> None:
        self._interval = interval
        self._max_candles = max_candles
        self._candles: list[Candle] = []

    @property
    def candles(self) -> tuple[Candle, ...]:
        return tuple(self._candles)

    def add_tick(self, price: Decimal, timestamp: datetime) -> None:
        """Fold one tick into the open candle for its bucket, opening a new
        candle when the tick starts a new interval. Ticks older than the
        current open candle (late/replayed delivery) are dropped rather
        than rewriting history out of order."""
        bucket_start = self._bucket_start(timestamp)
        if self._candles:
            last = self._candles[-1]
            if bucket_start == last.start:
                self._candles[-1] = replace(
                    last, high=max(last.high, price), low=min(last.low, price), close=price,
                )
                return
            if bucket_start < last.start:
                return
        self._candles.append(Candle(start=bucket_start, open=price, high=price, low=price, close=price))
        if len(self._candles) > self._max_candles:
            self._candles.pop(0)

    def add_tick_payload(self, tick: dict) -> bool:
        """Parse a raw tick payload dict (as delivered by MarketViewModel's
        tick_updated signal -- ltp/timestamp serialized via Pydantic's
        mode="json", so ltp arrives as a numeric string and timestamp as an
        ISO 8601 string) and fold it in. Returns False without mutating
        state when ltp is missing or malformed, rather than raising -- a
        single bad tick shouldn't break the live chart."""
        price = self._parse_price(tick.get("ltp"))
        if price is None:
            return False
        self.add_tick(price, self._parse_timestamp(tick.get("timestamp")))
        return True

    def clear(self) -> None:
        self._candles.clear()

    def _bucket_start(self, timestamp: datetime) -> datetime:
        seconds = self._interval.total_seconds()
        epoch = timestamp.timestamp()
        bucket_epoch = epoch - (epoch % seconds)
        return datetime.fromtimestamp(bucket_epoch, tz=timestamp.tzinfo or timezone.utc)

    @staticmethod
    def _parse_price(raw: object) -> Decimal | None:
        if raw is None:
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _parse_timestamp(raw: object) -> datetime:
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                pass
        return datetime.now(timezone.utc)
