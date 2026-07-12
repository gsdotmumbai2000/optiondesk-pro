"""Strategy aggregate model."""

from dataclasses import dataclass

from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata


@dataclass(frozen=True, slots=True)
class Strategy:
    """Immutable strategy as a collection of legs."""

    metadata: StrategyMetadata
    legs: tuple[StrategyLeg, ...]

    @property
    def strategy_id(self) -> str:
        """Return strategy identifier."""
        return self.metadata.strategy_id
