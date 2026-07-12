"""Performance metrics models."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    """Aggregated performance metrics."""

    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    calmar_ratio: Decimal
    profit_factor: Decimal
    expectancy: Decimal
    recovery_factor: Decimal
    return_on_capital: Decimal
    win_rate: Decimal
    loss_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    max_consecutive_wins: int
    max_consecutive_losses: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_holding_time: timedelta
    capital_utilization: Decimal
    margin_utilization: Decimal
