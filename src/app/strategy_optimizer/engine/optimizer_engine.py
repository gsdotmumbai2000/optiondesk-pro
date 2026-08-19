"""Optimizer engine."""

from datetime import datetime, timezone
from decimal import Decimal

from app.strategy_optimizer.constraints.checker import ConstraintChecker
from app.strategy_optimizer.engine.ports import EvaluationPort
from app.strategy_optimizer.engine.request_builder import build_evaluation_request
from app.strategy_optimizer.filters.candidate_filter import CandidateFilter
from app.strategy_optimizer.generators.candidate_generator import CandidateGenerator
from app.strategy_optimizer.models.candidate import CandidateStrategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.models.result import OptimizationResult
from app.strategy_optimizer.objectives.weighter import ObjectiveWeighter
from app.strategy_optimizer.ranking.ranker import StrategyRanker
from app.strategy_optimizer.scoring.scorer import greeks_summary, score_evaluation
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator
from app.strategy_optimizer.search.registry import resolve_search_algorithm


class OptimizerEngine:
    """Enterprise strategy optimizer engine."""

    def __init__(
        self,
        evaluator: EvaluationPort,
        generator: CandidateGenerator | None = None,
        constraint_checker: ConstraintChecker | None = None,
        candidate_filter: CandidateFilter | None = None,
        ranker: StrategyRanker | None = None,
        objective_weighter: ObjectiveWeighter | None = None,
    ) -> None:
        """Initialize with injected dependencies."""
        self._evaluator = evaluator
        self._generator = generator or CandidateGenerator()
        self._constraints = constraint_checker or ConstraintChecker()
        self._filter = candidate_filter or CandidateFilter()
        self._ranker = ranker or StrategyRanker()
        self._objectives = objective_weighter or ObjectiveWeighter()

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """Run full optimization pipeline."""
        ctx = request.calculation_context
        all_candidates = self._generator.generate(ctx)
        search = resolve_search_algorithm(request.preferences.search_algorithm)
        fitness = CandidateFitnessEvaluator(self._evaluator, request)
        search_space = search.search(all_candidates, request, fitness)

        eval_requests = tuple(
            build_evaluation_request(s, request) for s in search_space
        )
        evaluations = self._evaluator.evaluate_batch(eval_requests)

        constrained = tuple(
            ev for ev in evaluations
            if self._constraints.passes(ev, request.constraints)
        )
        filtered = self._filter.filter(constrained, request)

        candidates: list[CandidateStrategy] = []
        for ev in filtered:
            score = score_evaluation(ev)
            candidates.append(
                CandidateStrategy(
                    evaluation=ev,
                    score=score,
                    greeks_summary=greeks_summary(ev),
                )
            )

        ranked = self._ranker.rank(tuple(candidates), request.preferences)
        return self._build_result(ranked, request)

    def _build_result(
        self,
        ranked: tuple[CandidateStrategy, ...],
        request: OptimizationRequest,
    ) -> OptimizationResult:
        if not ranked:
            from app.strategy_optimizer.models.candidate import GreeksSummary

            return OptimizationResult(
                candidate_strategies=(),
                overall_score=Decimal("0"),
                expected_return=Decimal("0"),
                expected_risk=Decimal("0"),
                probability_of_profit=Decimal("0"),
                capital_required=Decimal("0"),
                margin_required=Decimal("0"),
                greeks_summary=GreeksSummary(
                    net_delta=Decimal("0"),
                    net_gamma=Decimal("0"),
                    net_theta=Decimal("0"),
                    net_vega=Decimal("0"),
                ),
                liquidity_score=Decimal("0"),
                recommendation="No candidates passed constraints",
                ranking=(),
                optimization_timestamp=datetime.now(timezone.utc),
            )
        best = ranked[0]
        ctx = best.evaluation.analysis.context
        rec = best.evaluation.recommendation.recommendation
        return OptimizationResult(
            candidate_strategies=ranked,
            overall_score=best.score.overall_score,
            expected_return=ctx.probability_result.expected_value,
            expected_risk=ctx.risk_result.value_at_risk,
            probability_of_profit=ctx.probability_result.probability_of_profit,
            capital_required=ctx.margin_result.capital_required,
            margin_required=ctx.margin_result.total_margin,
            greeks_summary=best.greeks_summary,
            liquidity_score=best.score.liquidity_score,
            recommendation=rec,
            ranking=tuple(c.evaluation.strategy.strategy_id for c in ranked),
            optimization_timestamp=datetime.now(timezone.utc),
        )
