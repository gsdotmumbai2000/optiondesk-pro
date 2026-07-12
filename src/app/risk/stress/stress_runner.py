"""Stress test runner."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.analytics.expiry_payoff import total_expiry_pnl
from app.payoff.models.legs import StrategyLeg
from app.risk.models.stress import StressScenario, StressTestResult
from app.volatility.models.volatility_result import VolatilityResult


def run_stress_test(
    scenario: StressScenario,
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    volatility: VolatilityResult,
    base_pnl: Decimal,
) -> StressTestResult:
    """Execute a single stress scenario and return loss."""
    price_factor = Decimal("1") + scenario.price_shift_pct / Decimal("100")
    shocked_price = context.spot_price * price_factor
    iv_factor = Decimal("1") + scenario.iv_shift_pct / Decimal("100")
    shocked_iv = volatility.implied_volatility * iv_factor
    stressed_pnl = total_expiry_pnl(shocked_price, legs)
    loss = base_pnl - stressed_pnl
    stress_loss = loss if loss > 0 else Decimal("0")
    return StressTestResult(
        scenario_id=scenario.scenario_id,
        stress_loss=stress_loss,
        shocked_price=shocked_price,
        shocked_iv=shocked_iv,
    )


def run_all_stress_tests(
    scenarios: tuple[StressScenario, ...],
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    volatility: VolatilityResult,
    base_pnl: Decimal,
) -> tuple[StressTestResult, ...]:
    """Run multiple stress scenarios."""
    return tuple(
        run_stress_test(s, legs, context, volatility, base_pnl) for s in scenarios
    )
