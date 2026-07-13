"""Background event dispatcher for live ticks."""

import hashlib
import queue
from collections.abc import Callable
from threading import Event, Thread
from typing import Protocol

from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.diagnostics import market_data_debug_enabled
from app.market_data.events import (
    FutureUpdatedEvent,
    OptionUpdatedEvent,
    PriceUpdatedEvent,
    QuoteUpdatedEvent,
    TickReceivedEvent,
)
from app.market_data.models.tick import TickSnapshot
from app.market_data.statistics.tick_statistics import TickStatistics

logger = get_logger(__name__)


class TickCacheWriter(Protocol):
    """Minimal cache interface for dispatcher."""

    def put_tick(self, tick: TickSnapshot) -> None:
        """Store tick."""


class EventDispatcher:
    """Queue ticks on websocket thread and publish on dispatcher thread."""

    def __init__(
        self,
        cache: TickCacheWriter,
        event_bus: EventBus | None = None,
        *,
        can_dispatch: Callable[[], bool] | None = None,
        max_queue: int = 50_000,
        statistics: TickStatistics | None = None,
    ) -> None:
        """Initialize dispatcher."""
        self._cache = cache
        self._event_bus = event_bus
        self._can_dispatch = can_dispatch or (lambda: True)
        self._fingerprints: dict[str, str] = {}
        self._queue: queue.Queue[TickSnapshot | None] = queue.Queue(maxsize=max_queue)
        self._stop = Event()
        self._statistics = statistics or TickStatistics()
        self._thread = Thread(target=self._worker, name="md-dispatcher", daemon=True)
        self._thread.start()

    @property
    def tick_count(self) -> int:
        """Return total ticks dispatched."""
        return self._statistics.total_ticks

    def enqueue(self, tick: TickSnapshot) -> bool:
        """Enqueue tick without blocking websocket thread."""
        if not self._can_dispatch():
            return False
        try:
            self._queue.put_nowait(tick)
            return True
        except queue.Full:
            logger.warning("Market data dispatcher queue full, dropping tick")
            self._statistics.record_drop()
            return False

    def dispatch(self, tick: TickSnapshot) -> bool:
        """Backward-compatible synchronous dispatch alias."""
        return self.enqueue(tick)

    def shutdown(self) -> None:
        """Stop dispatcher thread."""
        self._stop.set()
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=2)

    def _worker(self) -> None:
        while not self._stop.is_set():
            tick = self._queue.get()
            if tick is None:
                continue
            self._process(tick)

    def _process(self, tick: TickSnapshot) -> None:
        fingerprint = self._fingerprint(tick)
        key = f"{tick.exchange}:{tick.symbol}:{tick.expiry_date}:{tick.strike_price}"
        if self._fingerprints.get(key) == fingerprint:
            return
        self._fingerprints[key] = fingerprint
        self._cache.put_tick(tick)
        if market_data_debug_enabled():
            logger.info(
                "[DISPATCHER] DISPATCHER TICK "
                "exchange={exchange} symbol={symbol} ltp={ltp} "
                "queue_size={queue_size} tick_count={tick_count}",
                exchange=tick.exchange,
                symbol=tick.symbol,
                ltp=tick.ltp,
                queue_size=self._queue.qsize(),
                tick_count=self._statistics.total_ticks + 1,
            )
        self._statistics.record_tick()
        self._publish_events(tick)
        if self._statistics.total_ticks % 500 == 0:
            logger.debug("Tick count: {count}", count=self._statistics.total_ticks)

    def _fingerprint(self, tick: TickSnapshot) -> str:
        parts = [
            tick.symbol,
            tick.exchange,
            str(tick.ltp),
            str(tick.volume),
            str(tick.timestamp),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def _publish_events(self, tick: TickSnapshot) -> None:
        if self._event_bus is None:
            return
        payload = {"tick": tick.model_dump(mode="json")}
        self._event_bus.publish(TickReceivedEvent(payload=payload))
        self._event_bus.publish(PriceUpdatedEvent(payload=payload))
        self._event_bus.publish(QuoteUpdatedEvent(payload=payload))
        if tick.product_type.upper() in {"OPTIONS", "OPTION"}:
            self._event_bus.publish(OptionUpdatedEvent(payload=payload))
        if tick.product_type.upper() in {"FUTURES", "FUTURE"}:
            self._event_bus.publish(FutureUpdatedEvent(payload=payload))
