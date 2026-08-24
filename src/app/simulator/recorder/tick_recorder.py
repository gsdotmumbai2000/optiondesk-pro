"""Tap the live tick stream and persist NIFTY-only ticks for later replay."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.events import TickReceivedEvent
from app.simulator.events import RecordingTickCapturedEvent

logger = get_logger(__name__)


class TickRecorder:
    """Subscribe to TickReceivedEvent and persist NIFTY-only ticks as JSONL.

    Taps TickReceivedEvent rather than PriceUpdatedEvent/QuoteUpdatedEvent/
    OptionUpdatedEvent because EventDispatcher publishes TickReceivedEvent
    exactly once per unique tick, while the other three would triplicate
    (or quadruplicate) every entry.
    """

    def __init__(
        self,
        event_bus: EventBus,
        output_dir: Path,
        *,
        symbol_prefix: str = "NIFTY",
    ) -> None:
        """Initialize recorder, opening today's recording file."""
        self._event_bus = event_bus
        self._symbol_prefix = symbol_prefix
        output_dir.mkdir(parents=True, exist_ok=True)
        self._path = output_dir / f"nifty_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self._lock = threading.Lock()
        self._tick_count = 0

    @property
    def output_path(self) -> Path:
        """Return the file being recorded to."""
        return self._path

    @property
    def tick_count(self) -> int:
        """Return number of ticks recorded so far."""
        return self._tick_count

    def start(self) -> None:
        """Subscribe to the live tick stream."""
        self._event_bus.subscribe(TickReceivedEvent, self._on_tick)
        logger.info("Tick recorder started, writing to {path}", path=self._path)

    def _on_tick(self, event: TickReceivedEvent) -> None:
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            return
        tick = payload.get("tick")
        if not isinstance(tick, dict):
            return
        symbol = str(tick.get("symbol", ""))
        if not symbol.startswith(self._symbol_prefix):
            return
        record = {"captured_at": datetime.now(timezone.utc).isoformat(), "tick": tick}
        with self._lock:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            self._tick_count += 1
            count = self._tick_count
        self._event_bus.publish(
            RecordingTickCapturedEvent(payload={"tick_count": count, "path": str(self._path)})
        )
