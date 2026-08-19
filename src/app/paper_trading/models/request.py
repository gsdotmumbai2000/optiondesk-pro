"""Paper order request model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.backtesting.models.enums import OrderSide
from app.strategy.models.leg import StrategyLeg


@dataclass(frozen=True, slots=True)
class PaperOrderRequest:
    """A simulated order against a specific strategy leg (option, future,
    or stock instrument). `side` is the order's own direction (independent
    of `leg.kind`, since the same instrument can be bought to open, sold to
    close, or shorted), so a single leg can be opened and later closed with
    two requests referencing the same instrument.

    `reference_price` is caller-supplied (e.g. the leg's quoted premium or
    a live snapshot's LTP) -- this module has no live-data dependency of
    its own; it simulates a fill *around* whatever price it's given."""

    leg: StrategyLeg
    side: OrderSide
    quantity: int
    reference_price: Decimal
    timestamp: datetime
