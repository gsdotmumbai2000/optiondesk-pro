"""Analytics service."""

from decimal import Decimal

from app.backtesting.analytics.performance import PerformanceAnalytics
from app.backtesting.models.metrics import PerformanceMetrics
from app.backtesting.models.trades import EquityCurve, TradeLog


class AnalyticsService:
    """Performance analytics service."""

    def __init__(self, analytics: PerformanceAnalytics | None = None) -> None:
        """Initialize analytics service."""
        self._analytics = analytics or PerformanceAnalytics()

    def analyze(
        self,
        trade_log: TradeLog,
        equity_curve: EquityCurve,
        initial_capital: Decimal,
    ) -> PerformanceMetrics:
        """Run performance analytics."""
        return self._analytics.analyze(trade_log, equity_curve, initial_capital)
