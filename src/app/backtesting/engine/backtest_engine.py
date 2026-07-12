"""Backtesting engine orchestrator."""

from datetime import datetime, timezone
from decimal import Decimal

from app.backtesting.analytics.performance import PerformanceAnalytics
from app.backtesting.engine.ports import EvaluationPort
from app.backtesting.execution.simulator import ExecutionSimulator, OrderRequest
from app.backtesting.models.enums import BacktestModelVersion, OrderSide, OrderType
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult
from app.backtesting.models.trades import EquityCurve, EquityPoint, Trade, TradeLog
from app.backtesting.portfolio.tracker import PortfolioTracker
from app.backtesting.replay.replay_engine import ReplayEngine


class BacktestEngine:
    """Orchestrate replay, execution, portfolio, and analytics."""

    def __init__(
        self,
        evaluator: EvaluationPort | None = None,
        analytics: PerformanceAnalytics | None = None,
    ) -> None:
        """Initialize with optional evaluation port."""
        self._evaluator = evaluator
        self._analytics = analytics or PerformanceAnalytics()

    def run(self, request: BacktestRequest) -> BacktestResult:
        """Run full backtest simulation."""
        params = request.parameters
        replay = ReplayEngine(request.market_data, request.option_chain_data)
        executor = ExecutionSimulator(params.execution)
        portfolio = PortfolioTracker(params.initial_capital)
        trades: list[Trade] = []
        equity_points: list[EquityPoint] = []

        replay.start(start_index=params.replay.start_index)
        end = params.replay.end_index or replay.total_bars

        while replay.current_index < end:
            event = replay.step_forward(params.replay.step_size)
            if event is None:
                break
            self._maybe_execute(request, event.bar.close, event.timestamp, executor, portfolio, trades)
            if request.strategy_context is not None:
                portfolio.update_margin(
                    request.strategy_context.margin_result.total_margin
                )
                portfolio.update_unrealized(
                    request.strategy_context.payoff_result.current_pnl
                )
            snap = portfolio.snapshot()
            equity_points.append(
                EquityPoint(timestamp=event.timestamp, equity=snap.equity)
            )

        trade_log = TradeLog(trades=tuple(trades))
        equity_curve = EquityCurve(points=tuple(equity_points))
        metrics = self._analytics.analyze(
            trade_log, equity_curve, params.initial_capital
        )
        dd_curve = self._analytics.build_drawdown_curve(equity_curve)
        stats = self._trade_stats(trade_log)
        final_equity = equity_curve.points[-1].equity if equity_curve.points else params.initial_capital
        net = final_equity - params.initial_capital
        total_return = net / params.initial_capital if params.initial_capital > 0 else Decimal("0")
        margin_util = (
            request.strategy_context.margin_result.margin_utilization
            if request.strategy_context
            else Decimal("0")
        )

        return BacktestResult(
            total_return=total_return,
            net_profit=net,
            gross_profit=stats["gross_profit"],
            gross_loss=stats["gross_loss"],
            maximum_drawdown=self._analytics.max_drawdown(equity_curve),
            profit_factor=metrics.profit_factor,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            calmar_ratio=metrics.calmar_ratio,
            expectancy=metrics.expectancy,
            win_rate=metrics.win_rate,
            loss_rate=metrics.loss_rate,
            average_win=metrics.average_win,
            average_loss=metrics.average_loss,
            largest_win=metrics.largest_win,
            largest_loss=metrics.largest_loss,
            maximum_consecutive_wins=metrics.max_consecutive_wins,
            maximum_consecutive_losses=metrics.max_consecutive_losses,
            total_trades=metrics.total_trades,
            winning_trades=metrics.winning_trades,
            losing_trades=metrics.losing_trades,
            average_holding_time=metrics.average_holding_time,
            capital_utilization=metrics.capital_utilization,
            margin_utilization=margin_util,
            equity_curve=equity_curve,
            drawdown_curve=dd_curve,
            trade_log=trade_log,
            performance_metrics=metrics,
            simulation_timestamp=datetime.now(timezone.utc),
            model_version=BacktestModelVersion.V1,
        )

    def _maybe_execute(
        self,
        request: BacktestRequest,
        price: Decimal,
        timestamp: datetime,
        executor: ExecutionSimulator,
        portfolio: PortfolioTracker,
        trades: list[Trade],
    ) -> None:
        if not request.strategy.legs:
            return
        if portfolio.snapshot().open_positions or trades:
            return
        for leg in request.strategy.legs:
            side = OrderSide.BUY if "BUY" in leg.kind.value else OrderSide.SELL
            order = OrderRequest(
                symbol=leg.underlying or request.market_data.underlying,
                side=side,
                order_type=OrderType.MARKET,
                quantity=abs(leg.quantity),
                price=price,
                timestamp=timestamp,
            )
            result = executor.execute(order)
            portfolio.apply_trade(result.trade)
            trades.append(result.trade)

    def _trade_stats(self, trade_log: TradeLog) -> dict:
        from app.backtesting.analytics.trade_stats import trade_statistics
        return trade_statistics(trade_log)
