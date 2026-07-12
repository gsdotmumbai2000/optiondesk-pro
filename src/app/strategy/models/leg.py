"""Strategy leg model."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.strategy.models.enums import LegKind


@dataclass(frozen=True, slots=True)
class StrategyLeg:
    """Immutable strategy leg supporting options, futures, and stock."""

    leg_id: str
    kind: LegKind
    quantity: int
    premium: Decimal
    strike: Decimal = Decimal("0")
    expiry: date | None = None
    multiplier: int = 1
    underlying: str = ""
    exchange: str = ""
