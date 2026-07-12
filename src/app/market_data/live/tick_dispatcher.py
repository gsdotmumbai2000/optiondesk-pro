"""Dispatch normalized ticks to cache and event bus."""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.events import TickReceivedEvent
from app.market_data.live.tick_cache import TickCache
from app.market_data.models.tick import TickSnapshot

logger = get_logger(__name__)


class TickDispatcher:
    """Route ticks with duplicate protection."""

    def __init__(self, cache: TickCache, event_bus: EventBus | None = None) -> None:
        """Initialize dispatcher."""
        self._cache = cache
        self._event_bus = event_bus
        self._fingerprints: dict[str, str] = {}
        self._tick_count = 0

    @property
    def tick_count(self) -> int:
        """Return total ticks dispatched."""
        return self._tick_count

    def dispatch(self, tick: TickSnapshot) -> bool:
        """Store tick and publish event if not duplicate."""
        fingerprint = self._fingerprint(tick)
        key = f"{tick.exchange}:{tick.symbol}:{tick.expiry_date}:{tick.strike_price}"
        if self._fingerprints.get(key) == fingerprint:
            return False
        self._fingerprints[key] = fingerprint
        self._cache.put(tick)
        self._tick_count += 1
        self._publish(tick)
        if self._tick_count % 100 == 0:
            logger.debug("Tick count: {count}", count=self._tick_count)
        return True

    def _fingerprint(self, tick: TickSnapshot) -> str:
        parts = [
            tick.symbol,
            tick.exchange,
            str(tick.ltp),
            str(tick.volume),
            str(tick.timestamp),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def _publish(self, tick: TickSnapshot) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            TickReceivedEvent(payload={"tick": tick.model_dump(mode="json")})
        )
