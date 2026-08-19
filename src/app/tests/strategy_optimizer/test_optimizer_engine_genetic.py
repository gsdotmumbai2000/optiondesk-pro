"""Integration test: OptimizerEngine.optimize() wired end-to-end with
GeneticAlgorithmSearch -- proves the engine actually constructs a
CandidateFitnessEvaluator and threads it through search() correctly, and
that the existing constraints/filter/score/rank pipeline downstream still
produces a coherent OptimizationResult when search_space comes from GA
instead of BruteForceSearch. Mirrors
test_optimizer_engine_simulated_annealing.py for the second real search
algorithm.
"""

from decimal import Decimal
from types import SimpleNamespace

from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.engine.optimizer_engine import OptimizerEngine
from app.strategy_optimizer.models.constraints import OptimizationConstraints
from app.strategy_optimizer.models.enums import OptimizationObjective, SearchAlgorithmType
from app.strategy_optimizer.models.preferences import OptimizationPreferences


def _strategy(strategy_id: str) -> Strategy:
    leg = StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_SELL, quantity=1, premium=Decimal("100"), strike=Decimal("24500"),
    )
    metadata = StrategyBuilder(name=strategy_id).build().metadata
    from dataclasses import replace

    return Strategy(metadata=replace(metadata, strategy_id=strategy_id), legs=(leg,))


class _FakeGenerator:
    """CandidateGenerator double: a small, controlled pool instead of the
    real ~130-candidate sweep, so this test runs fast and stays focused on
    engine wiring rather than GA's own search behavior (covered separately
    in test_genetic_search.py)."""

    def __init__(self, count: int = 10) -> None:
        self.candidates = tuple(_strategy(str(i)) for i in range(count))

    def generate(self, context) -> tuple[Strategy, ...]:
        return self.candidates


def _fake_evaluation(strategy: Strategy, overall_score: Decimal) -> SimpleNamespace:
    risk = SimpleNamespace(
        maximum_drawdown=Decimal("10"), net_delta=Decimal("0.1"), net_gamma=Decimal("0.01"),
        net_vega=Decimal("2"), net_theta=Decimal("-1"), value_at_risk=Decimal("500"),
    )
    margin = SimpleNamespace(
        total_margin=Decimal("9000"), capital_required=Decimal("9000"),
        margin_utilization=Decimal("0.3"), capital_efficiency=Decimal("70"),
    )
    # probability_of_profit tracks overall_score (not a flat constant) so the
    # MAX_POP-weighted fitness GA's search() uses internally actually agrees
    # with the overall_score the outer ranker sorts by -- a flat internal
    # landscape would make elitism/tournament selection directionless.
    probability = SimpleNamespace(
        probability_of_profit=Decimal("0.5") + overall_score / Decimal("100"), expected_value=Decimal("500"),
    )
    volatility = SimpleNamespace(iv_percentile=Decimal("40"))
    context = SimpleNamespace(risk_result=risk, margin_result=margin, probability_result=probability, volatility_result=volatility)
    score = SimpleNamespace(risk_score=Decimal("60"), reward_score=Decimal("70"), overall_score=overall_score)
    analysis = SimpleNamespace(context=context, score=score, liquidity_score=Decimal("80"))
    recommendation = SimpleNamespace(recommendation="Consider this strategy")
    return SimpleNamespace(strategy=strategy, analysis=analysis, recommendation=recommendation)


class _FakeEvaluator:
    """EvaluationPort double: overall_score is derived from the strategy_id
    when it parses as an int (original pool candidates); crossover children
    carry a synthesized id, so they fall back to a fixed mid-range score --
    still a real, deterministic evaluation, just not tied to the original
    numbering."""

    def __init__(self) -> None:
        self.evaluate_calls = 0

    def evaluate(self, request):
        self.evaluate_calls += 1
        strategy = request.strategy
        try:
            score = Decimal(strategy.strategy_id)
        except Exception:
            score = Decimal("5")
        return _fake_evaluation(strategy, overall_score=score)

    def evaluate_batch(self, requests):
        return tuple(self.evaluate(r) for r in requests)


def _request_stub() -> SimpleNamespace:
    return SimpleNamespace(
        calculation_context=SimpleNamespace(),
        option_contract=SimpleNamespace(),
        option_chain=SimpleNamespace(),
        market_snapshot=SimpleNamespace(),
        chain_market_snapshot=SimpleNamespace(),
        volatility_market_snapshot=SimpleNamespace(),
        historical_data=SimpleNamespace(),
    )


def _optimization_request(algorithm: SearchAlgorithmType) -> SimpleNamespace:
    preferences = OptimizationPreferences(
        underlying="NIFTY", expiry="18-Aug-2026", capital=Decimal("1000000"),
        market_outlook="NEUTRAL", risk_preference="MODERATE",
        primary_objective=OptimizationObjective.MAX_POP,
        search_algorithm=algorithm, max_candidates=1000,
    )
    base = _request_stub()
    return SimpleNamespace(
        **base.__dict__,
        preferences=preferences,
        constraints=OptimizationConstraints(),  # fully permissive
    )


class TestOptimizerEngineWithGeneticAlgorithm:
    def test_produces_a_ranked_result_without_crashing(self) -> None:
        generator = _FakeGenerator(count=15)
        engine = OptimizerEngine(evaluator=_FakeEvaluator(), generator=generator)
        request = _optimization_request(SearchAlgorithmType.GENETIC)

        result = engine.optimize(request)

        assert len(result.candidate_strategies) > 0
        assert result.ranking
        assert all(isinstance(sid, str) for sid in result.ranking)

    def test_best_candidate_matches_highest_overall_score(self) -> None:
        generator = _FakeGenerator(count=15)
        engine = OptimizerEngine(evaluator=_FakeEvaluator(), generator=generator)
        request = _optimization_request(SearchAlgorithmType.GENETIC)

        result = engine.optimize(request)

        assert result.ranking[0] == "14"  # highest strategy_id -> highest overall_score

    def test_search_algorithm_is_actually_used_fewer_evaluations_than_brute_force(self) -> None:
        """GA explores a bounded population/generation budget, unlike
        BruteForceSearch which evaluates every candidate -- proves the
        fitness-driven search path is genuinely wired in, not silently
        falling back to evaluating everything."""
        generator = _FakeGenerator(count=200)
        ga_evaluator = _FakeEvaluator()
        ga_engine = OptimizerEngine(evaluator=ga_evaluator, generator=generator)
        ga_request = _optimization_request(SearchAlgorithmType.GENETIC)
        ga_engine.optimize(ga_request)

        brute_evaluator = _FakeEvaluator()
        brute_engine = OptimizerEngine(evaluator=brute_evaluator, generator=generator)
        brute_request = _optimization_request(SearchAlgorithmType.BRUTE_FORCE)
        brute_engine.optimize(brute_request)

        assert ga_evaluator.evaluate_calls < brute_evaluator.evaluate_calls
