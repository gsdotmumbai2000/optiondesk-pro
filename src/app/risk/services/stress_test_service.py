"""Stress test application service."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.models.legs import StrategyLeg
from app.risk.engine.stress_calculator import StressCalculator
from app.risk.models.stress import StressScenario, StressTestResult
from app.risk.stress.stress_scenarios import all_stress_scenarios
from app.volatility.models.volatility_result import VolatilityResult


class StressTestService:
    """Service for stress testing."""

    def __init__(self, calculator: StressCalculator | None = None) -> None:
        """Initialize service."""
        self._calculator = calculator or StressCalculator()

    def run_all(
        self,
        legs: tuple[StrategyLeg, ...],
        context: CalculationContext,
        volatility: VolatilityResult,
        base_pnl: Decimal,
    ) -> tuple[StressTestResult, ...]:
        """Run all predefined stress scenarios."""
        return self._calculator.run(
            all_stress_scenarios(), legs, context, volatility, base_pnl
        )

    def run_custom(
        self,
        scenarios: tuple[StressScenario, ...],
        legs: tuple[StrategyLeg, ...],
        context: CalculationContext,
        volatility: VolatilityResult,
        base_pnl: Decimal,
    ) -> tuple[StressTestResult, ...]:
        """Run custom stress scenarios."""
        return self._calculator.run(scenarios, legs, context, volatility, base_pnl)
