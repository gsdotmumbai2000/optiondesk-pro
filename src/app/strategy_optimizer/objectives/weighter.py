"""Objective weighting from preferences."""

from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.enums import OptimizationObjective
from app.strategy_optimizer.models.preferences import OptimizationPreferences


class ObjectiveWeighter:
    """Weight evaluations by optimization objective."""

    def weight(
        self,
        evaluation: StrategyEvaluation,
        preferences: OptimizationPreferences,
    ) -> Decimal:
        """Return objective-weighted score from engine outputs."""
        ctx = evaluation.analysis.context
        scores = evaluation.analysis.score
        objective = preferences.primary_objective
        mapping = {
            OptimizationObjective.MAX_POP: ctx.probability_result.probability_of_profit,
            OptimizationObjective.MAX_EXPECTED_RETURN: ctx.probability_result.expected_value,
            OptimizationObjective.MIN_RISK: Decimal("100") - scores.risk_score,
            OptimizationObjective.MIN_MARGIN: Decimal("100") - ctx.margin_result.margin_utilization * Decimal("100"),
            OptimizationObjective.MAX_THETA: abs(ctx.risk_result.net_theta),
            OptimizationObjective.DELTA_NEUTRAL: Decimal("100") - abs(ctx.risk_result.net_delta),
            OptimizationObjective.MIN_VEGA: Decimal("100") - abs(ctx.risk_result.net_vega),
            OptimizationObjective.MAX_CAPITAL_EFFICIENCY: ctx.margin_result.capital_efficiency,
            OptimizationObjective.MIN_DRAWDOWN: Decimal("100") - ctx.risk_result.maximum_drawdown,
        }
        return mapping.get(objective, scores.overall_score)
