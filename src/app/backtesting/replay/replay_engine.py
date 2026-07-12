"""Historical replay engine."""

from dataclasses import dataclass
from datetime import datetime

from app.backtesting.models.enums import ReplaySpeed, ReplayState
from app.backtesting.models.historical import (
    HistoricalMarketData,
    HistoricalOptionChainData,
    HistoricalOptionChainSnapshot,
)
from app.market_data.models.snapshot import HistoricalBar


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """Single replay step event."""

    index: int
    bar: HistoricalBar
    chain: HistoricalOptionChainSnapshot | None
    timestamp: datetime


class ReplayEngine:
    """Replay historical candles and option chains."""

    def __init__(
        self,
        market_data: HistoricalMarketData,
        option_chain_data: HistoricalOptionChainData,
    ) -> None:
        """Initialize replay engine."""
        self._bars = market_data.bars
        self._chains = {s.timestamp: s for s in option_chain_data.snapshots}
        self._index = 0
        self._state = ReplayState.IDLE
        self._speed = ReplaySpeed.X1

    @property
    def state(self) -> ReplayState:
        """Return current replay state."""
        return self._state

    @property
    def speed(self) -> ReplaySpeed:
        """Return replay speed."""
        return self._speed

    @property
    def total_bars(self) -> int:
        """Return total bar count."""
        return len(self._bars)

    @property
    def current_index(self) -> int:
        """Return current bar index."""
        return self._index

    def start(self, *, start_index: int = 0) -> None:
        """Start replay from index."""
        self._index = start_index
        self._state = ReplayState.RUNNING

    def pause(self) -> None:
        """Pause replay."""
        if self._state == ReplayState.RUNNING:
            self._state = ReplayState.PAUSED

    def resume(self) -> None:
        """Resume paused replay."""
        if self._state == ReplayState.PAUSED:
            self._state = ReplayState.RUNNING

    def set_speed(self, speed: ReplaySpeed) -> None:
        """Set replay speed."""
        self._speed = speed

    def step_forward(self, steps: int = 1) -> ReplayEvent | None:
        """Advance one or more bars."""
        if self._index >= len(self._bars):
            self._state = ReplayState.FINISHED
            return None
        step = self._resolve_step(steps)
        bar = self._bars[self._index]
        chain = self._chains.get(bar.timestamp)
        event = ReplayEvent(
            index=self._index,
            bar=bar,
            chain=chain,
            timestamp=bar.timestamp,
        )
        self._index += step
        if self._index >= len(self._bars):
            self._state = ReplayState.FINISHED
        return event

    def fast_forward(self, to_index: int) -> ReplayEvent | None:
        """Jump to bar index."""
        self._index = min(to_index, len(self._bars) - 1)
        return self.step_forward(0) if self._index < len(self._bars) else None

    def _resolve_step(self, steps: int) -> int:
        multipliers = {
            ReplaySpeed.X1: 1,
            ReplaySpeed.X2: 2,
            ReplaySpeed.X5: 5,
            ReplaySpeed.X10: 10,
            ReplaySpeed.MAX: 100,
        }
        return steps * multipliers.get(self._speed, 1)
