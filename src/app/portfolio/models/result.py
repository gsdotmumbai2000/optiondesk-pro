"""Portfolio analysis result."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.portfolio.models.enums import PortfolioModelVersion
from app.portfolio.models.performance import PortfolioAllocation, PortfolioPerformance
from app.portfolio.models.positions import Position
from app.portfolio.models.transactions import Trade, Transaction


@dataclass(frozen=True, slots=True)
class GreeksSummary:
    """Portfolio greeks from risk engine (no local calculation)."""

    net_delta: Decimal
    net_gamma: Decimal
    net_theta: Decimal
    net_vega: Decimal


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Portfolio risk from risk engine."""

    value_at_risk: Decimal
    risk_score: Decimal
    capital_at_risk: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioResult:
    """Immutable portfolio analytics output."""

    portfolio_value: Decimal
    cash_balance: Decimal
    available_cash: Decimal
    used_margin: Decimal
    available_margin: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    todays_pnl: Decimal
    daily_return: Decimal
    total_return: Decimal
    greeks_summary: GreeksSummary
    risk_summary: RiskSummary
    open_positions: tuple[Position, ...]
    closed_positions: tuple[Position, ...]
    open_orders: tuple[Trade, ...]
    transaction_history: tuple[Transaction, ...]
    performance_summary: PortfolioPerformance
    allocation: PortfolioAllocation
    calculation_timestamp: datetime
    model_version: PortfolioModelVersion = PortfolioModelVersion.V1
