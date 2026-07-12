"""Strategy builder."""

from datetime import datetime, timezone

from app.strategy.models.enums import StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata
from app.strategy.models.strategy import Strategy
from app.utils.uuid_helper import generate_uuid


class StrategyBuilder:
    """Build and modify strategies from legs."""

    def __init__(
        self,
        metadata: StrategyMetadata | None = None,
        name: str = "Custom Strategy",
    ) -> None:
        """Initialize builder."""
        self._legs: list[StrategyLeg] = []
        self._metadata = metadata
        self._name = name

    @property
    def legs(self) -> tuple[StrategyLeg, ...]:
        """Return current legs."""
        return tuple(self._legs)

    def add_leg(self, leg: StrategyLeg) -> "StrategyBuilder":
        """Add a leg to the strategy."""
        self._legs.append(leg)
        return self

    def remove_leg(self, leg_id: str) -> "StrategyBuilder":
        """Remove a leg by identifier."""
        self._legs = [leg for leg in self._legs if leg.leg_id != leg_id]
        return self

    def modify_leg(self, leg_id: str, updated: StrategyLeg) -> "StrategyBuilder":
        """Replace a leg by identifier."""
        self._legs = [
            updated if leg.leg_id == leg_id else leg for leg in self._legs
        ]
        return self

    def clone(self) -> "StrategyBuilder":
        """Clone builder with copied legs."""
        clone = StrategyBuilder(self._metadata, self._name)
        clone._legs = list(self._legs)
        return clone

    def from_strategy(self, strategy: Strategy) -> "StrategyBuilder":
        """Load legs from existing strategy."""
        self._legs = list(strategy.legs)
        self._metadata = strategy.metadata
        self._name = strategy.metadata.name
        return self

    def build(self) -> Strategy:
        """Build immutable strategy."""
        now = datetime.now(timezone.utc)
        if self._metadata is not None:
            metadata = self._metadata
        else:
            metadata = StrategyMetadata(
                strategy_id=generate_uuid(),
                name=self._name,
                recognized_type=StrategyType.CUSTOM,
                created_at=now,
                updated_at=now,
            )
        return Strategy(metadata=metadata, legs=tuple(self._legs))
