"""Stress test calculator."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.models.legs import StrategyLeg
from app.risk.models.stress import StressScenario, StressTestResult
from app.risk.stress.stress_runner import run_all_stress_tests, run_stress_test
from app.volatility.models.volatility_result import VolatilityResult


class StressCalculator:
    """Execute stress tests on portfolio."""

    def run(
        self,
        scenarios: tuple[StressScenario, ...],
        legs: tuple[StrategyLeg, ...],
        context: CalculationContext,
        volatility: VolatilityResult,
        base_pnl: Decimal,
    ) -> tuple[StressTestResult, ...]:
        """Run stress scenarios."""
        return run_all_stress_tests(scenarios, legs, context, volatility, base_pnl)

    def run_single(
        self,
        scenario: StressScenario,
        legs: tuple[StrategyLeg, ...],
        context: CalculationContext,
        volatility: VolatilityResult,
        base_pnl: Decimal,
    ) -> StressTestResult:
        """Run a single stress scenario."""
        return run_stress_test(scenario, legs, context, volatility, base_pnl)
