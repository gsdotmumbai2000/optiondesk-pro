"""Report data models."""

from dataclasses import dataclass

from app.portfolio.models.performance import PortfolioAllocation, PortfolioPerformance
from app.portfolio.models.transactions import Transaction


@dataclass(frozen=True, slots=True)
class PortfolioReport:
    """Portfolio summary report."""

    portfolio_id: str
    portfolio_value: str
    cash_balance: str


@dataclass(frozen=True, slots=True)
class TransactionReport:
    """Transaction history report."""

    transactions: tuple[Transaction, ...]
    total_count: int


@dataclass(frozen=True, slots=True)
class PnLReport:
    """Profit and loss report."""

    realized_pnl: str
    unrealized_pnl: str
    todays_pnl: str


@dataclass(frozen=True, slots=True)
class AllocationReport:
    """Allocation report."""

    allocation: PortfolioAllocation


@dataclass(frozen=True, slots=True)
class PerformanceReport:
    """Performance report."""

    performance: PortfolioPerformance
