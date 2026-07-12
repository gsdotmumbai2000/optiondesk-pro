"""Optimization constraint models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OptimizationConstraints:
    """Configurable optimization constraints."""

    max_loss: Decimal | None = None
    max_margin: Decimal | None = None
    min_pop: Decimal | None = None
    min_liquidity: Decimal | None = None
    max_delta: Decimal | None = None
    max_gamma: Decimal | None = None
    max_vega: Decimal | None = None
    max_position_size: int | None = None
    max_legs: int | None = None
