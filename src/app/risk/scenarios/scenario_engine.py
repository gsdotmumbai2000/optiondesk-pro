"""Scenario engine for risk analysis."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.analytics.expiry_payoff import total_expiry_pnl
from app.payoff.models.legs import StrategyLeg
from app.risk.models.scenario import (
    RiskScenario,
    RiskScenarioResult,
    ScenarioComparison,
    ScenarioRanking,
)


def run_scenario(
    scenario: RiskScenario,
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    base_pnl: Decimal,
) -> RiskScenarioResult:
    """Execute a single risk scenario."""
    factor = Decimal("1") + scenario.price_shift_pct / Decimal("100")
    shocked_price = context.spot_price * factor
    stressed_pnl = total_expiry_pnl(shocked_price, legs)
    change = stressed_pnl - base_pnl
    loss = -change if change < 0 else Decimal("0")
    return RiskScenarioResult(
        scenario_id=scenario.scenario_id,
        scenario_loss=loss,
        pnl_change=change,
    )


def run_scenarios(
    scenarios: tuple[RiskScenario, ...],
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    base_pnl: Decimal,
) -> tuple[RiskScenarioResult, ...]:
    """Execute multiple risk scenarios."""
    return tuple(run_scenario(s, legs, context, base_pnl) for s in scenarios)


def compare_scenarios(
    results: tuple[RiskScenarioResult, ...],
) -> ScenarioComparison:
    """Compare scenario results and identify best/worst."""
    if not results:
        return ScenarioComparison(scenarios=(), worst_case_id="", best_case_id="")
    worst = max(results, key=lambda r: r.scenario_loss)
    best = min(results, key=lambda r: r.scenario_loss)
    return ScenarioComparison(
        scenarios=results,
        worst_case_id=worst.scenario_id,
        best_case_id=best.scenario_id,
    )


def rank_scenarios(
    results: tuple[RiskScenarioResult, ...],
) -> ScenarioRanking:
    """Rank scenarios by loss severity."""
    ranked = sorted(results, key=lambda r: r.scenario_loss, reverse=True)
    with_rank = tuple(
        RiskScenarioResult(
            scenario_id=r.scenario_id,
            scenario_loss=r.scenario_loss,
            pnl_change=r.pnl_change,
            rank=idx + 1,
        )
        for idx, r in enumerate(ranked)
    )
    return ScenarioRanking(ranked=with_rank)
