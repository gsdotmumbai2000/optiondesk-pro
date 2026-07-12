"""Portfolio engine entry point."""

from datetime import datetime, timezone
from decimal import Decimal

from app.portfolio.analytics.allocation import AllocationCalculator
from app.portfolio.analytics.greeks_adapter import GreeksAdapter
from app.portfolio.analytics.margin_adapter import MarginAdapter
from app.portfolio.analytics.risk_adapter import RiskAdapter
from app.portfolio.engine.state_builder import PortfolioStateBuilder
from app.portfolio.models.portfolio import Portfolio
from app.portfolio.models.request import PortfolioAnalysisRequest
from app.portfolio.models.result import PortfolioResult
from app.portfolio.performance.calculator import PerformanceCalculator


class PortfolioEngine:
    """Enterprise portfolio management engine."""

    def __init__(self) -> None:
        """Initialize engine components."""
        self._state = PortfolioStateBuilder()
        self._greeks = GreeksAdapter()
        self._risk = RiskAdapter()
        self._margin = MarginAdapter()
        self._allocation = AllocationCalculator()
        self._performance = PerformanceCalculator()

    def calculate(
        self,
        request: PortfolioAnalysisRequest,
        portfolio: Portfolio,
        value_history: tuple[Decimal, ...] = (),
        initial_capital: Decimal = Decimal("0"),
    ) -> tuple[Portfolio, PortfolioResult]:
        """Build portfolio result from request and state."""
        updated = self._state.apply_trades(portfolio, request.trade_executions)
        updated = self._state.apply_broker_updates(updated, request.broker_updates)
        result = self._build_result(
            updated,
            request,
            value_history,
            initial_capital,
        )
        return updated, result

    def _build_result(
        self,
        portfolio: Portfolio,
        request: PortfolioAnalysisRequest,
        value_history: tuple[Decimal, ...],
        initial_capital: Decimal,
    ) -> PortfolioResult:
        cash = portfolio.cash_account
        holdings_value = sum(h.market_value for h in portfolio.holdings)
        portfolio_value = holdings_value
        realized = sum(p.realized_pnl for p in portfolio.closed_positions)
        unrealized = sum(p.unrealized_pnl for p in portfolio.open_positions)
        used_margin, available_margin = self._margin.extract(
            request.margin_result,
            cash.available,
        )
        perf = self._performance.calculate(
            value_history,
            initial_capital or cash.balance,
            realized,
            request.backtest_result,
        )
        daily = perf.daily_return
        total_ret = perf.annual_return
        if request.backtest_result:
            total_ret = request.backtest_result.total_return
        return PortfolioResult(
            portfolio_value=portfolio_value,
            cash_balance=cash.balance,
            available_cash=cash.available,
            used_margin=used_margin,
            available_margin=available_margin,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            todays_pnl=daily * portfolio_value,
            daily_return=daily,
            total_return=total_ret,
            greeks_summary=self._greeks.from_risk(request.risk_result),
            risk_summary=self._risk.from_risk(request.risk_result),
            open_positions=portfolio.open_positions,
            closed_positions=portfolio.closed_positions,
            open_orders=portfolio.pending_orders,
            transaction_history=portfolio.transactions,
            performance_summary=perf,
            allocation=self._allocation.calculate(portfolio.holdings),
            calculation_timestamp=datetime.now(timezone.utc),
        )
