"""Margin optimizer."""

from decimal import Decimal

from app.margin.models.optimization import MarginOptimizationResult
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult
from app.margin.optimization.suggestions import generate_suggestions


class MarginOptimizer:
    """Margin optimization framework."""

    def optimize(
        self,
        request: MarginAnalysisRequest,
        result: MarginResult,
    ) -> MarginOptimizationResult:
        """Run margin optimization analysis."""
        account = request.context.spot_price * Decimal(
            request.context.lot_size
        ) * Decimal("10")
        unused = max(account - result.total_margin, Decimal("0"))
        score = self._efficiency_score(result)
        optimized = result.total_margin - result.margin_benefit * Decimal("0.1")
        suggestions = generate_suggestions(
            request.resolved_legs,
            request.context,
            result.total_margin,
        )
        return MarginOptimizationResult(
            capital_efficiency_score=score,
            unused_capital=unused,
            current_margin=result.total_margin,
            optimized_margin_estimate=max(optimized, Decimal("0")),
            suggestions=suggestions,
        )

    def _efficiency_score(self, result: MarginResult) -> Decimal:
        raw = result.capital_efficiency * Decimal("50")
        util_penalty = result.margin_utilization * Decimal("25")
        score = raw - util_penalty + Decimal("50")
        return min(max(score, Decimal("0")), Decimal("100"))
