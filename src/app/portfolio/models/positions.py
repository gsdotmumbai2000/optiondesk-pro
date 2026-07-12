"""Position and holding models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.portfolio.models.enums import AssetClass, PositionStatus


@dataclass(frozen=True, slots=True)
class Holding:
    """Immutable holding record."""

    holding_id: str
    symbol: str
    asset_class: AssetClass
    quantity: int
    average_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    underlying: str = ""


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable position record."""

    position_id: str
    symbol: str
    asset_class: AssetClass
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    status: PositionStatus
    opened_at: datetime
    closed_at: datetime | None = None
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
