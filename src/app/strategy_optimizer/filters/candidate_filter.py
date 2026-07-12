"""Candidate filters from engine outputs."""

from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.request import OptimizationRequest


class CandidateFilter:
    """Filter candidates using engine results and market data."""

    def filter(
        self,
        evaluations: tuple[StrategyEvaluation, ...],
        request: OptimizationRequest,
    ) -> tuple[StrategyEvaluation, ...]:
        """Apply all filters."""
        result: list[StrategyEvaluation] = []
        capital = request.preferences.capital
        for ev in evaluations:
            if self._passes_capital(ev, capital):
                result.append(ev)
        return tuple(result)

    def _passes_capital(
        self,
        evaluation: StrategyEvaluation,
        capital: Decimal,
    ) -> bool:
        required = evaluation.analysis.context.margin_result.capital_required
        return required <= capital
