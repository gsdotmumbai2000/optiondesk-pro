"""Replay service."""

from app.backtesting.models.historical import (
    HistoricalMarketData,
    HistoricalOptionChainData,
)
from app.backtesting.models.enums import ReplaySpeed
from app.backtesting.replay.replay_engine import ReplayEngine


class ReplayService:
    """Manage replay sessions."""

    def create(
        self,
        market_data: HistoricalMarketData,
        option_chain_data: HistoricalOptionChainData,
    ) -> ReplayEngine:
        """Create replay engine instance."""
        return ReplayEngine(market_data, option_chain_data)

    def set_speed(self, engine: ReplayEngine, speed: ReplaySpeed) -> None:
        """Set replay speed."""
        engine.set_speed(speed)
