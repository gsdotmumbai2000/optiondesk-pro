"""Alternative strategy builder from optimization engine."""

from decimal import Decimal

from app.ai.models.alternative import AlternativeStrategy
from app.ai.models.request import RecommendationAnalysisRequest


class AlternativeStrategyBuilder:
    """Extract alternatives from optimization result (no calculation)."""

    def build(
        self,
        request: RecommendationAnalysisRequest,
        limit: int = 3,
    ) -> tuple[AlternativeStrategy, ...]:
        """Build alternative strategies from optimizer output."""
        opt = request.optimization_result
        if opt is None or not opt.candidate_strategies:
            return ()
        alts: list[AlternativeStrategy] = []
        for candidate in opt.candidate_strategies[:limit]:
            ev = candidate.evaluation
            alts.append(
                AlternativeStrategy(
                    strategy_id=ev.strategy.strategy_id,
                    label=ev.strategy.name,
                    expected_return=opt.expected_return,
                    probability_of_profit=ev.analysis.probability_of_profit,
                    capital_required=opt.capital_required,
                    rationale=opt.recommendation,
                )
            )
        return tuple(alts)
