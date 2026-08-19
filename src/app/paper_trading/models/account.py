"""Paper trading account models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.backtesting.models.enums import OrderSide
from app.strategy.models.leg import StrategyLeg


@dataclass(frozen=True, slots=True)
class PaperPosition:
    """Open paper position for one instrument. `quantity` is signed:
    positive is long, negative is short."""

    position_id: str
    leg: StrategyLeg
    quantity: int
    average_entry_price: Decimal
    opened_at: datetime


@dataclass(frozen=True, slots=True)
class PaperTrade:
    """Executed paper trade record."""

    trade_id: str
    leg: StrategyLeg
    side: OrderSide
    quantity: int
    fill_price: Decimal
    commission: Decimal
    slippage: Decimal
    timestamp: datetime
    realized_pnl: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class PaperAccountSnapshot:
    """Point-in-time paper account state."""

    account_id: str
    initial_capital: Decimal
    cash_balance: Decimal
    open_positions: tuple[PaperPosition, ...]
    realized_pnl: Decimal
    equity: Decimal
