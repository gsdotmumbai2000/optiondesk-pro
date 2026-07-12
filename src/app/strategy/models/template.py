"""Strategy template model."""

from dataclasses import dataclass

from app.strategy.models.enums import StrategyType
from app.strategy.models.leg import StrategyLeg


@dataclass(frozen=True, slots=True)
class StrategyTemplate:
    """Immutable strategy template."""

    template_id: str
    name: str
    strategy_type: StrategyType
    legs: tuple[StrategyLeg, ...]
    description: str = ""
    is_builtin: bool = True
