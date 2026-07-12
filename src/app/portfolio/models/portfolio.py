"""Portfolio aggregate models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.portfolio.models.cash import CashAccount
from app.portfolio.models.enums import PortfolioModelVersion
from app.portfolio.models.positions import Holding, Position
from app.portfolio.models.transactions import Trade, Transaction


@dataclass(frozen=True, slots=True)
class Portfolio:
    """Immutable portfolio aggregate."""

    portfolio_id: str
    name: str
    cash_account: CashAccount
    holdings: tuple[Holding, ...]
    open_positions: tuple[Position, ...]
    closed_positions: tuple[Position, ...]
    pending_orders: tuple[Trade, ...]
    executed_orders: tuple[Trade, ...]
    transactions: tuple[Transaction, ...]
    version: PortfolioModelVersion = PortfolioModelVersion.V1


@dataclass(frozen=True, slots=True)
class PortfolioSummary:
    """High-level portfolio summary."""

    portfolio_id: str
    portfolio_value: Decimal
    cash_balance: Decimal
    holdings_count: int
    open_positions_count: int


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """Point-in-time portfolio snapshot."""

    portfolio_id: str
    captured_at: datetime
    portfolio_value: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
