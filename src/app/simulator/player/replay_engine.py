"""Replay a recorded NIFTY tick session into the live EventDispatcher.

Feeds TickSnapshot objects straight into the same EventDispatcher instance
the real broker path uses, so cache population and event fan-out
(TickReceivedEvent/PriceUpdatedEvent/QuoteUpdatedEvent/OptionUpdatedEvent)
happen identically to a live tick. Consumers (LiveAnalyticsService, the
enterprise MarketDataEngine, MarketDataService) need no changes.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market_data.dispatcher.event_dispatcher import EventDispatcher
from app.market_data.models.tick import TickSnapshot

logger = get_logger(__name__)


def find_latest_recording(directory: Path, pattern: str = "nifty_*.jsonl") -> Path | None:
    """Return the most recently named recording file in directory, if any."""
    if not directory.exists():
        return None
    candidates = sorted(directory.glob(pattern))
    return candidates[-1] if candidates else None


class ReplayEngine:
    """Loop a recorded tick session at real-time pacing into the dispatcher."""

    def __init__(
        self,
        dispatcher: EventDispatcher,
        recording_path: Path,
        *,
        min_interval_seconds: float = 0.05,
    ) -> None:
        """Initialize replay engine for one recording file."""
        self._dispatcher = dispatcher
        self._recording_path = recording_path
        self._min_interval = min_interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._entries: list[dict] = []

    def start(self) -> None:
        """Load the recording and start looped real-time replay."""
        self._entries = self._load_entries(self._recording_path)
        if not self._entries:
            logger.warning(
                "No recorded ticks found at {path}; simulator has nothing to replay",
                path=self._recording_path,
            )
            return
        self._thread = threading.Thread(target=self._run, name="simulator-replay", daemon=True)
        self._thread.start()
        logger.info(
            "Simulator replay started: {count} ticks from {path}",
            count=len(self._entries),
            path=self._recording_path,
        )

    def stop(self) -> None:
        """Stop replay and join the background thread."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    @staticmethod
    def _load_entries(path: Path) -> list[dict]:
        if not path.exists():
            return []
        entries: list[dict] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def _run(self) -> None:
        while not self._stop.is_set():
            previous_captured_at: datetime | None = None
            for entry in self._entries:
                if self._stop.is_set():
                    return
                captured_at = self._parse_captured_at(entry.get("captured_at"))
                if previous_captured_at is not None and captured_at is not None:
                    gap = (captured_at - previous_captured_at).total_seconds()
                    self._stop.wait(max(gap, self._min_interval))
                previous_captured_at = captured_at
                self._replay_tick(entry.get("tick"))

    def _replay_tick(self, tick_dict: object) -> None:
        if not isinstance(tick_dict, dict):
            return
        refreshed = dict(tick_dict)
        refreshed["timestamp"] = datetime.now(timezone.utc).isoformat()
        try:
            tick = TickSnapshot.model_validate(refreshed)
        except Exception as error:
            logger.warning("Skipping unreplayable recorded tick: {error}", error=error)
            return
        self._dispatcher.enqueue(tick)

    @staticmethod
    def _parse_captured_at(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
