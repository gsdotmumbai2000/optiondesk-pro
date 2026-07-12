"""Trade and curve models."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.backtesting.models.enums import OrderSide, OrderType


@dataclass(frozen=True, slots=True)
class Trade:
    """Immutable executed trade record."""

    trade_id: str
    timestamp: datetime
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Decimal
    commission: Decimal
    slippage: Decimal
    pnl: Decimal
    holding_time: timedelta


@dataclass(frozen=True, slots=True)
class TradeLog:
    """Collection of executed trades."""

    trades: tuple[Trade, ...]


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """Single equity curve point."""

    timestamp: datetime
    equity: Decimal


@dataclass(frozen=True, slots=True)
class EquityCurve:
    """Equity curve time series."""

    points: tuple[EquityPoint, ...]


@dataclass(frozen=True, slots=True)
class DrawdownPoint:
    """Single drawdown curve point."""

    timestamp: datetime
    drawdown: Decimal


@dataclass(frozen=True, slots=True)
class DrawdownCurve:
    """Drawdown curve time series."""

    points: tuple[DrawdownPoint, ...]
