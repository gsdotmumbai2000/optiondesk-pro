"""Performance application service."""

from decimal import Decimal

from app.backtesting.models.result import BacktestResult
from app.portfolio.models.performance import PortfolioPerformance
from app.portfolio.performance.calculator import PerformanceCalculator


class PerformanceService:
    """Expose performance calculations."""

    def __init__(self, calculator: PerformanceCalculator | None = None) -> None:
        """Initialize service."""
        self._calculator = calculator or PerformanceCalculator()

    def calculate(
        self,
        value_series: tuple[Decimal, ...],
        initial_capital: Decimal,
        realized_pnl: Decimal,
        backtest: BacktestResult | None = None,
    ) -> PortfolioPerformance:
        """Calculate performance summary."""
        return self._calculator.calculate(
            value_series,
            initial_capital,
            realized_pnl,
            backtest,
        )
