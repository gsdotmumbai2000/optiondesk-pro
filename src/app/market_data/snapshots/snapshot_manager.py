"""Market snapshot manager."""

from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from app.market_data.models import MarketSnapshot, OptionChain, Quote, SnapshotKind


class SnapshotManager:
    """Manage current, previous, and delta snapshots."""

    def __init__(self) -> None:
        """Initialize snapshot storage."""
        self._lock = RLock()
        self._current: MarketSnapshot | None = None
        self._previous: MarketSnapshot | None = None

    @property
    def current(self) -> MarketSnapshot | None:
        """Return current snapshot."""
        with self._lock:
            return self._current

    @property
    def previous(self) -> MarketSnapshot | None:
        """Return previous snapshot."""
        with self._lock:
            return self._previous

    def capture(
        self,
        quotes: dict[str, Quote],
        chains: dict[str, OptionChain] | None = None,
    ) -> MarketSnapshot:
        """Capture a new snapshot and rotate previous."""
        snapshot = MarketSnapshot(
            snapshot_id=str(uuid4()),
            snapshot_kind=SnapshotKind.CURRENT,
            captured_at=datetime.now(timezone.utc),
            quotes=quotes,
            chains=chains or {},
        )
        with self._lock:
            self._previous = self._current
            self._current = snapshot
        return snapshot

    def delta(self) -> MarketSnapshot | None:
        """Return delta between current and previous snapshots."""
        with self._lock:
            if self._current is None or self._previous is None:
                return None
            delta_quotes = {
                key: quote
                for key, quote in self._current.quotes.items()
                if key not in self._previous.quotes
                or self._previous.quotes[key].ltp != quote.ltp
            }
            return MarketSnapshot(
                snapshot_id=str(uuid4()),
                snapshot_kind=SnapshotKind.DELTA,
                captured_at=datetime.now(timezone.utc),
                quotes=delta_quotes,
            )
