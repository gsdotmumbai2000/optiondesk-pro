"""Holding application service."""

from decimal import Decimal

from app.portfolio.holdings.aggregator import HoldingAggregator
from app.portfolio.models.positions import Holding, Position


class HoldingService:
    """Expose holding aggregation."""

    def __init__(self, aggregator: HoldingAggregator | None = None) -> None:
        """Initialize service."""
        self._aggregator = aggregator or HoldingAggregator()

    def from_positions(self, positions: tuple[Position, ...]) -> tuple[Holding, ...]:
        """Build holdings from positions."""
        return self._aggregator.from_positions(positions)

    def cash_holding(self, balance: Decimal, currency: str = "INR") -> Holding:
        """Create cash holding."""
        return self._aggregator.cash_holding(balance, currency)
