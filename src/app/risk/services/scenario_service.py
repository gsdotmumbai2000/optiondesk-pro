"""Scenario application service."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.models.legs import StrategyLeg
from app.risk.models.scenario import (
    RiskScenario,
    RiskScenarioResult,
    ScenarioComparison,
    ScenarioRanking,
)
from app.risk.scenarios.scenario_engine import (
    compare_scenarios,
    rank_scenarios,
    run_scenarios,
)


class ScenarioService:
    """Service for risk scenario analysis."""

    def run(
        self,
        scenarios: tuple[RiskScenario, ...],
        legs: tuple[StrategyLeg, ...],
        context: CalculationContext,
        base_pnl: Decimal,
    ) -> tuple[RiskScenarioResult, ...]:
        """Run multiple scenarios."""
        return run_scenarios(scenarios, legs, context, base_pnl)

    def compare(
        self,
        results: tuple[RiskScenarioResult, ...],
    ) -> ScenarioComparison:
        """Compare scenario results."""
        return compare_scenarios(results)

    def rank(
        self,
        results: tuple[RiskScenarioResult, ...],
    ) -> ScenarioRanking:
        """Rank scenarios by severity."""
        return rank_scenarios(results)
