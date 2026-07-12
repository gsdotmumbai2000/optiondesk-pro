"""Portfolio position models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.strategy.models.leg import StrategyLeg


@dataclass(frozen=True, slots=True)
class OpenPosition:
    """Open portfolio position."""

    position_id: str
    leg: StrategyLeg
    quantity: int
    entry_price: Decimal
    entry_time: datetime
    unrealized_pnl: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class ClosedPosition:
    """Closed portfolio position."""

    position_id: str
    leg: StrategyLeg
    quantity: int
    entry_price: Decimal
    exit_price: Decimal
    entry_time: datetime
    exit_time: datetime
    realized_pnl: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """Point-in-time portfolio state."""

    cash_balance: Decimal
    margin_usage: Decimal
    open_positions: tuple[OpenPosition, ...]
    closed_positions: tuple[ClosedPosition, ...]
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    equity: Decimal
