"""Report data models."""

from dataclasses import dataclass

from app.backtesting.models.trades import DrawdownCurve, EquityCurve, TradeLog


@dataclass(frozen=True, slots=True)
class TradeReport:
    """Trade report data model."""

    trade_log: TradeLog
    total_trades: int


@dataclass(frozen=True, slots=True)
class MonthlyPerformance:
    """Monthly performance bucket."""

    period: str
    return_pct: str
    trades: int


@dataclass(frozen=True, slots=True)
class YearlyPerformance:
    """Yearly performance bucket."""

    year: str
    return_pct: str
    trades: int


@dataclass(frozen=True, slots=True)
class BacktestReport:
    """Full backtest report."""

    trade_report: TradeReport
    equity_curve: EquityCurve
    drawdown_curve: DrawdownCurve
    monthly: tuple[MonthlyPerformance, ...]
    yearly: tuple[YearlyPerformance, ...]
