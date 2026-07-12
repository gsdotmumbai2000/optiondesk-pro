"""Constraint checking from engine outputs."""

from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.constraints import OptimizationConstraints


class ConstraintChecker:
    """Check candidates against optimization constraints."""

    def passes(
        self,
        evaluation: StrategyEvaluation,
        constraints: OptimizationConstraints,
    ) -> bool:
        """Return True if evaluation passes all constraints."""
        ctx = evaluation.analysis.context
        risk = ctx.risk_result
        margin = ctx.margin_result
        prob = ctx.probability_result
        analysis = evaluation.analysis
        legs = evaluation.strategy.legs

        checks = [
            self._check_max_loss(risk.maximum_drawdown, constraints.max_loss),
            self._check_max(margin.total_margin, constraints.max_margin),
            self._check_min(prob.probability_of_profit, constraints.min_pop),
            self._check_min(analysis.liquidity_score, constraints.min_liquidity),
            self._check_max(abs(risk.net_delta), constraints.max_delta),
            self._check_max(abs(risk.net_gamma), constraints.max_gamma),
            self._check_max(abs(risk.net_vega), constraints.max_vega),
            self._check_max_legs(len(legs), constraints.max_legs),
        ]
        return all(checks)

    def _check_max(self, actual: Decimal, limit: Decimal | None) -> bool:
        if limit is None:
            return True
        return actual <= limit

    def _check_min(self, actual: Decimal, limit: Decimal | None) -> bool:
        if limit is None:
            return True
        return actual >= limit

    def _check_max_loss(self, drawdown: Decimal, limit: Decimal | None) -> bool:
        if limit is None:
            return True
        return drawdown <= limit

    def _check_max_legs(self, count: int, limit: int | None) -> bool:
        if limit is None:
            return True
        return count <= limit
