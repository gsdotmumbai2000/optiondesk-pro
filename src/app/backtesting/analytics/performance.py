"""Performance analytics from trade and equity data."""

from datetime import datetime, timedelta
from decimal import Decimal

from app.backtesting.models.metrics import PerformanceMetrics
from app.backtesting.models.trades import DrawdownCurve, DrawdownPoint, EquityCurve, EquityPoint, TradeLog
from app.backtesting.analytics.ratios import calmar_ratio, sharpe_ratio, sortino_ratio
from app.backtesting.analytics.trade_stats import trade_statistics


class PerformanceAnalytics:
    """Calculate backtest performance metrics."""

    def analyze(
        self,
        trade_log: TradeLog,
        equity_curve: EquityCurve,
        initial_capital: Decimal,
    ) -> PerformanceMetrics:
        """Compute full performance metrics."""
        stats = trade_statistics(trade_log)
        returns = self._equity_returns(equity_curve)
        sharpe = sharpe_ratio(returns)
        sortino = sortino_ratio(returns)
        max_dd = self.max_drawdown(equity_curve)
        calmar = calmar_ratio(returns, max_dd)
        net = equity_curve.points[-1].equity - initial_capital if equity_curve.points else Decimal("0")
        roc = net / initial_capital if initial_capital > 0 else Decimal("0")
        recovery = net / max_dd if max_dd > 0 else Decimal("0")
        return PerformanceMetrics(
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            profit_factor=stats["profit_factor"],
            expectancy=stats["expectancy"],
            recovery_factor=recovery,
            return_on_capital=roc,
            win_rate=stats["win_rate"],
            loss_rate=stats["loss_rate"],
            average_win=stats["average_win"],
            average_loss=stats["average_loss"],
            largest_win=stats["largest_win"],
            largest_loss=stats["largest_loss"],
            max_consecutive_wins=stats["max_consecutive_wins"],
            max_consecutive_losses=stats["max_consecutive_losses"],
            total_trades=stats["total_trades"],
            winning_trades=stats["winning_trades"],
            losing_trades=stats["losing_trades"],
            average_holding_time=stats["average_holding_time"],
            capital_utilization=stats["capital_utilization"],
            margin_utilization=Decimal("0"),
        )

    def build_drawdown_curve(self, equity_curve: EquityCurve) -> DrawdownCurve:
        """Build drawdown curve from equity."""
        if not equity_curve.points:
            return DrawdownCurve(points=())
        peak = equity_curve.points[0].equity
        points: list[DrawdownPoint] = []
        for pt in equity_curve.points:
            if pt.equity > peak:
                peak = pt.equity
            dd = (peak - pt.equity) / peak if peak > 0 else Decimal("0")
            points.append(DrawdownPoint(timestamp=pt.timestamp, drawdown=dd))
        return DrawdownCurve(points=tuple(points))

    def max_drawdown(self, equity_curve: EquityCurve) -> Decimal:
        """Return maximum drawdown from equity curve."""
        dd_curve = self.build_drawdown_curve(equity_curve)
        if not dd_curve.points:
            return Decimal("0")
        return max(pt.drawdown for pt in dd_curve.points)

    def _equity_returns(self, curve: EquityCurve) -> tuple[Decimal, ...]:
        if len(curve.points) < 2:
            return ()
        returns: list[Decimal] = []
        for i in range(1, len(curve.points)):
            prev = curve.points[i - 1].equity
            curr = curve.points[i].equity
            if prev > 0:
                returns.append((curr - prev) / prev)
        return tuple(returns)
