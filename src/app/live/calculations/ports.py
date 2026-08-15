"""Live calculation pipeline ports."""

from typing import Protocol

from app.strategy.models.leg import StrategyLeg


class ActiveStrategyPort(Protocol):
    """Read-only access to the currently active strategy's legs."""

    def get_active_strategy_legs(self) -> tuple[StrategyLeg, ...]:
        """Return the active strategy's legs, or () when no strategy is active."""
