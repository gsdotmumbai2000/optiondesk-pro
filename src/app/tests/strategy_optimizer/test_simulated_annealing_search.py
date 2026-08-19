"""Tests for SimulatedAnnealingSearch: the one search algorithm that
actually uses real per-candidate fitness feedback (via a
CandidateFitnessEvaluator double here, isolating SA's own control flow from
CandidateFitnessEvaluator's own tested behavior) to walk the candidate
space, rather than just slicing a fixed list like BruteForceSearch/
HeuristicSearch.
"""

import random
from decimal import Decimal
from types import SimpleNamespace

from app.strategy.models.enums import StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.search.simulated_annealing import SimulatedAnnealingSearch


class _FakeFitness:
    """CandidateFitnessEvaluator double: fixed scores by strategy_id, so
    tests can construct a known fitness landscape."""

    def __init__(self, scores: dict[str, Decimal | None]) -> None:
        self._scores = scores
        self.call_count = 0

    def score(self, strategy: Strategy):
        self.call_count += 1
        return self._scores.get(strategy.strategy_id)


def _strategy(strategy_id: str, stype: StrategyType = StrategyType.LONG_CALL) -> Strategy:
    return Strategy(
        metadata=StrategyMetadata(strategy_id=strategy_id, name=strategy_id, recognized_type=stype),
        legs=(StrategyLeg(leg_id="L1", kind=None, quantity=1, premium=Decimal("0"), strike=Decimal("100")),),
    )


def _request(max_candidates: int = 1000) -> SimpleNamespace:
    return SimpleNamespace(preferences=SimpleNamespace(max_candidates=max_candidates))


class TestEmptyAndDegenerateInputs:
    def test_empty_candidates_returns_empty_tuple(self) -> None:
        search = SimulatedAnnealingSearch(rng=random.Random(1))

        result = search.search((), _request(), _FakeFitness({}))

        assert result == ()

    def test_all_candidates_fail_evaluation_returns_empty_tuple(self) -> None:
        candidates = (_strategy("A"), _strategy("B"), _strategy("C"))
        search = SimulatedAnnealingSearch(rng=random.Random(1))
        fitness = _FakeFitness({"A": None, "B": None, "C": None})

        result = search.search(candidates, _request(), fitness)

        assert result == ()

    def test_single_candidate_pool_does_not_crash(self) -> None:
        candidates = (_strategy("A"),)
        search = SimulatedAnnealingSearch(rng=random.Random(1))
        fitness = _FakeFitness({"A": Decimal("50")})

        result = search.search(candidates, _request(), fitness)

        assert result == (candidates[0],)


class TestResultsAreDrawnFromRealEvaluations:
    def test_every_returned_candidate_was_actually_scored(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(20))
        scores = {str(i): Decimal(i) for i in range(20)}
        search = SimulatedAnnealingSearch(rng=random.Random(7))
        fitness = _FakeFitness(scores)

        result = search.search(candidates, _request(), fitness)

        assert len(result) > 0
        returned_ids = {c.strategy_id for c in result}
        assert returned_ids <= {c.strategy_id for c in candidates}  # no fabricated strategies

    def test_best_candidate_found_is_included_in_the_result(self) -> None:
        """The single-peak fitness landscape's true best must survive into
        the final ranked result -- SA always tracks and returns the best
        it has seen, not just wherever the walk ended up."""
        candidates = tuple(_strategy(str(i)) for i in range(30))
        scores = {str(i): Decimal(i) for i in range(30)}  # candidate "29" is the unique best
        search = SimulatedAnnealingSearch(rng=random.Random(42))
        fitness = _FakeFitness(scores)

        result = search.search(candidates, _request(), fitness)

        assert result[0].strategy_id == "29"  # highest score ranked first

    def test_result_size_respects_max_candidates_cap(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(50))
        scores = {str(i): Decimal(i) for i in range(50)}
        search = SimulatedAnnealingSearch(rng=random.Random(3))
        fitness = _FakeFitness(scores)

        result = search.search(candidates, _request(max_candidates=5), fitness)

        assert len(result) <= 5


class TestDeterminismWithSeededRng:
    def test_same_seed_produces_same_result(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(15))
        scores = {str(i): Decimal(i % 7) for i in range(15)}

        result_a = SimulatedAnnealingSearch(rng=random.Random(99)).search(
            candidates, _request(), _FakeFitness(scores)
        )
        result_b = SimulatedAnnealingSearch(rng=random.Random(99)).search(
            candidates, _request(), _FakeFitness(scores)
        )

        assert [c.strategy_id for c in result_a] == [c.strategy_id for c in result_b]

    def test_fitness_is_not_recomputed_for_a_candidate_already_visited(self) -> None:
        """visited caching: a candidate the walk revisits must not trigger
        a second real evaluation -- fitness.score() is the expensive part
        (a full engine evaluation in production)."""
        candidates = tuple(_strategy(str(i)) for i in range(3))  # small pool -> guaranteed revisits
        scores = {str(i): Decimal(i) for i in range(3)}
        search = SimulatedAnnealingSearch(rng=random.Random(5))
        fitness = _FakeFitness(scores)

        search.search(candidates, _request(), fitness)

        # At most one score() call per distinct candidate (3) plus the
        # initial pick -- far fewer than the 150-iteration budget would
        # need without caching.
        assert fitness.call_count <= len(candidates) + 1
