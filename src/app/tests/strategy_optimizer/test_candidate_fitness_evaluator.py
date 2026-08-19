"""Tests for CandidateFitnessEvaluator: the real per-candidate scoring path
Simulated Annealing (and, potentially, future search algorithms) uses to get
fitness feedback -- unlike BruteForceSearch/HeuristicSearch, which never
touch evaluation at all since OptimizerEngine.optimize() runs search()
before evaluation.
"""

from decimal import Decimal
from types import SimpleNamespace

from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.exceptions import InvalidStrategyInput
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.enums import OptimizationObjective
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator


def _strategy() -> Strategy:
    leg = StrategyLeg(leg_id="L1", kind=LegKind.CALL_SELL, quantity=1, premium=Decimal("100"), strike=Decimal("24500"))
    return Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=(leg,))


def _fake_evaluation(*, overall_score=Decimal("50"), pop=Decimal("0.6")) -> SimpleNamespace:
    """Mimics StrategyEvaluation's exact attribute path ObjectiveWeighter
    and score_evaluation() read: analysis.context.<engine_result> and
    analysis.score.<field>."""
    context = SimpleNamespace(
        probability_result=SimpleNamespace(probability_of_profit=pop, expected_value=Decimal("500")),
        margin_result=SimpleNamespace(margin_utilization=Decimal("0.3"), capital_efficiency=Decimal("70")),
        risk_result=SimpleNamespace(net_theta=Decimal("-10"), net_delta=Decimal("0.2"), net_vega=Decimal("5"), maximum_drawdown=Decimal("20")),
    )
    analysis = SimpleNamespace(context=context, score=SimpleNamespace(overall_score=overall_score, risk_score=Decimal("40")))
    return SimpleNamespace(analysis=analysis)


class _FakeEvaluator:
    def __init__(self, evaluation=None, error: Exception | None = None) -> None:
        self.evaluation = evaluation or _fake_evaluation()
        self.error = error
        self.received_requests: list = []

    def evaluate(self, request):
        self.received_requests.append(request)
        if self.error is not None:
            raise self.error
        return self.evaluation

    def evaluate_batch(self, requests):
        raise AssertionError("not exercised by CandidateFitnessEvaluator")


def _request(objective: OptimizationObjective = OptimizationObjective.MAX_POP) -> SimpleNamespace:
    """Duck-typed OptimizationRequest: build_evaluation_request() and
    ObjectiveWeighter.weight() only read the attributes exercised below."""
    return SimpleNamespace(
        calculation_context=SimpleNamespace(),
        option_contract=SimpleNamespace(),
        option_chain=SimpleNamespace(),
        market_snapshot=SimpleNamespace(),
        chain_market_snapshot=SimpleNamespace(),
        volatility_market_snapshot=SimpleNamespace(),
        historical_data=SimpleNamespace(),
        preferences=SimpleNamespace(primary_objective=objective),
    )


class TestCandidateFitnessEvaluatorSuccess:
    def test_returns_objective_weighted_score(self) -> None:
        evaluator = _FakeEvaluator(_fake_evaluation(pop=Decimal("0.75")))
        request = _request(OptimizationObjective.MAX_POP)
        fitness = CandidateFitnessEvaluator(evaluator, request)

        score = fitness.score(_strategy())

        assert score == Decimal("0.75")  # raw probability_of_profit, per ObjectiveWeighter's MAX_POP mapping

    def test_falls_back_to_overall_score_for_unmapped_objective(self) -> None:
        evaluator = _FakeEvaluator(_fake_evaluation(overall_score=Decimal("88")))
        request = _request(objective="NOT_A_REAL_OBJECTIVE")
        fitness = CandidateFitnessEvaluator(evaluator, request)

        score = fitness.score(_strategy())

        assert score == Decimal("88")

    def test_builds_evaluation_request_from_the_given_strategy(self) -> None:
        evaluator = _FakeEvaluator()
        request = _request()
        fitness = CandidateFitnessEvaluator(evaluator, request)
        strategy = _strategy()

        fitness.score(strategy)

        assert len(evaluator.received_requests) == 1
        assert evaluator.received_requests[0].strategy is strategy


class TestCandidateFitnessEvaluatorFailure:
    def test_invalid_strategy_input_returns_none_not_raises(self) -> None:
        evaluator = _FakeEvaluator(error=InvalidStrategyInput("leg quantity cannot be zero"))
        fitness = CandidateFitnessEvaluator(evaluator, _request())

        assert fitness.score(_strategy()) is None
