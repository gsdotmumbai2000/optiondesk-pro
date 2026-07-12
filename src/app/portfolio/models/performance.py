"""Performance and statistics models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PortfolioPerformance:
    """Portfolio performance metrics."""

    daily_return: Decimal
    weekly_return: Decimal
    monthly_return: Decimal
    annual_return: Decimal
    cagr: Decimal
    drawdown: Decimal
    recovery: Decimal
    return_on_capital: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioStatistics:
    """Aggregate portfolio statistics."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    average_trade_pnl: Decimal


@dataclass(frozen=True, slots=True)
class AllocationSlice:
    """Single allocation bucket."""

    label: str
    weight: Decimal
    notional: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioAllocation:
    """Portfolio allocation breakdown."""

    asset: tuple[AllocationSlice, ...]
    underlying: tuple[AllocationSlice, ...]
    sector: tuple[AllocationSlice, ...]
    expiry: tuple[AllocationSlice, ...]
    capital: tuple[AllocationSlice, ...]
