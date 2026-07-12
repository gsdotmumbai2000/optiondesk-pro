"""Report builder."""

from app.backtesting.models.reports import (
    BacktestReport,
    MonthlyPerformance,
    TradeReport,
    YearlyPerformance,
)
from app.backtesting.models.result import BacktestResult


class ReportBuilder:
    """Build backtest report data models."""

    def build(self, result: BacktestResult) -> BacktestReport:
        """Build full backtest report."""
        return BacktestReport(
            trade_report=TradeReport(
                trade_log=result.trade_log,
                total_trades=result.total_trades,
            ),
            equity_curve=result.equity_curve,
            drawdown_curve=result.drawdown_curve,
            monthly=(),
            yearly=(),
        )

    def monthly_performance(
        self,
        result: BacktestResult,
    ) -> tuple[MonthlyPerformance, ...]:
        """Build monthly performance buckets (framework)."""
        return ()

    def yearly_performance(
        self,
        result: BacktestResult,
    ) -> tuple[YearlyPerformance, ...]:
        """Build yearly performance buckets (framework)."""
        return ()
