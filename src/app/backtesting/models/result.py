"""Backtest result."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.backtesting.models.enums import BacktestModelVersion
from app.backtesting.models.metrics import PerformanceMetrics
from app.backtesting.models.trades import DrawdownCurve, EquityCurve, TradeLog


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Immutable backtest output."""

    total_return: Decimal
    net_profit: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    maximum_drawdown: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    calmar_ratio: Decimal
    expectancy: Decimal
    win_rate: Decimal
    loss_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    maximum_consecutive_wins: int
    maximum_consecutive_losses: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_holding_time: timedelta
    capital_utilization: Decimal
    margin_utilization: Decimal
    equity_curve: EquityCurve
    drawdown_curve: DrawdownCurve
    trade_log: TradeLog
    performance_metrics: PerformanceMetrics
    simulation_timestamp: datetime
    model_version: BacktestModelVersion = BacktestModelVersion.V1
