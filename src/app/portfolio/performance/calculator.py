"""Portfolio performance aggregator."""

from decimal import Decimal

from app.backtesting.models.result import BacktestResult
from app.portfolio.models.performance import PortfolioPerformance
from app.portfolio.performance.cagr import CagrCalculator
from app.portfolio.performance.drawdown import DrawdownCalculator
from app.portfolio.performance.returns import ReturnCalculator


class PerformanceCalculator:
    """Aggregate portfolio performance metrics."""

    def __init__(self) -> None:
        """Initialize calculators."""
        self._returns = ReturnCalculator()
        self._drawdown = DrawdownCalculator()
        self._cagr = CagrCalculator()

    def calculate(
        self,
        value_series: tuple[Decimal, ...],
        initial_capital: Decimal,
        realized_pnl: Decimal,
        backtest: BacktestResult | None = None,
    ) -> PortfolioPerformance:
        """Build performance summary from value history."""
        if backtest is not None:
            return self._from_backtest(backtest)
        end = value_series[-1] if value_series else initial_capital
        return PortfolioPerformance(
            daily_return=self._returns.daily_return(value_series),
            weekly_return=self._returns.weekly_return(value_series),
            monthly_return=self._returns.monthly_return(value_series),
            annual_return=self._returns.annual_return(value_series),
            cagr=self._cagr.cagr(
                initial_capital,
                end,
                max(len(value_series) - 1, 1),
            ),
            drawdown=self._drawdown.drawdown(value_series),
            recovery=self._drawdown.recovery(value_series),
            return_on_capital=self._cagr.return_on_capital(
                realized_pnl,
                initial_capital,
            ),
        )

    def _from_backtest(self, backtest: BacktestResult) -> PortfolioPerformance:
        zero = Decimal("0")
        return PortfolioPerformance(
            daily_return=zero,
            weekly_return=zero,
            monthly_return=zero,
            annual_return=backtest.total_return,
            cagr=backtest.total_return,
            drawdown=backtest.maximum_drawdown,
            recovery=zero,
            return_on_capital=backtest.capital_utilization,
        )
