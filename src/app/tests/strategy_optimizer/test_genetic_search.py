"""Tests for GeneticAlgorithmSearch: the second search algorithm (after SA)
that uses real per-candidate fitness feedback (via a CandidateFitnessEvaluator
double here, isolating GA's own control flow) to evolve the candidate space,
rather than just slicing a fixed list like BruteForceSearch/HeuristicSearch.
"""

import random
from decimal import Decimal
from types import SimpleNamespace

from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.search.genetic import GeneticAlgorithmSearch


class _FakeFitness:
    """CandidateFitnessEvaluator double: fixed scores by strategy_id, so
    tests can construct a known fitness landscape. Crossover children get
    fresh strategy_ids not present in `scores` -- default them to a score
    derived from their own legs so the landscape stays evaluable."""

    def __init__(self, scores: dict[str, Decimal | None]) -> None:
        self._scores = scores
        self.call_count = 0

    def score(self, strategy: Strategy):
        self.call_count += 1
        if strategy.strategy_id in self._scores:
            return self._scores[strategy.strategy_id]
        return Decimal(sum(int(leg.strike) for leg in strategy.legs))


def _strategy(strategy_id: str, stype: StrategyType = StrategyType.LONG_CALL) -> Strategy:
    return Strategy(
        metadata=StrategyMetadata(strategy_id=strategy_id, name=strategy_id, recognized_type=stype),
        legs=(StrategyLeg(leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("0"), strike=Decimal("100")),),
    )


def _spread(strategy_id: str, low_strike: int, high_strike: int) -> Strategy:
    """Two-leg bull-call-spread-shaped strategy, so crossover between two
    of these actually has something structurally compatible to recombine."""
    return Strategy(
        metadata=StrategyMetadata(
            strategy_id=strategy_id, name=strategy_id, recognized_type=StrategyType.BULL_CALL_SPREAD
        ),
        legs=(
            StrategyLeg(
                leg_id=f"{strategy_id}-low", kind=LegKind.CALL_BUY, quantity=1,
                premium=Decimal("0"), strike=Decimal(low_strike),
            ),
            StrategyLeg(
                leg_id=f"{strategy_id}-high", kind=LegKind.CALL_SELL, quantity=1,
                premium=Decimal("0"), strike=Decimal(high_strike),
            ),
        ),
    )


def _request(max_candidates: int = 1000) -> SimpleNamespace:
    return SimpleNamespace(preferences=SimpleNamespace(max_candidates=max_candidates))


class TestEmptyAndDegenerateInputs:
    def test_empty_candidates_returns_empty_tuple(self) -> None:
        search = GeneticAlgorithmSearch(rng=random.Random(1))

        result = search.search((), _request(), _FakeFitness({}))

        assert result == ()

    def test_all_candidates_fail_evaluation_returns_empty_tuple(self) -> None:
        candidates = (_strategy("A"), _strategy("B"), _strategy("C"))
        search = GeneticAlgorithmSearch(rng=random.Random(1))
        fitness = _FakeFitness({"A": None, "B": None, "C": None})

        result = search.search(candidates, _request(), fitness)

        assert result == ()

    def test_single_candidate_pool_does_not_crash(self) -> None:
        candidates = (_strategy("A"),)
        search = GeneticAlgorithmSearch(rng=random.Random(1))
        fitness = _FakeFitness({"A": Decimal("50")})

        result = search.search(candidates, _request(), fitness)

        assert result == (candidates[0],)


class TestResultsAreDrawnFromRealEvaluations:
    def test_every_returned_candidate_was_actually_scored(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(20))
        scores = {str(i): Decimal(i) for i in range(20)}
        search = GeneticAlgorithmSearch(rng=random.Random(7))
        fitness = _FakeFitness(scores)

        result = search.search(candidates, _request(), fitness)

        assert len(result) > 0
        assert all(c.strategy_id in scores for c in result)  # single-leg pool: no crossover children

    def test_best_candidate_found_is_included_in_the_result(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(30))
        scores = {str(i): Decimal(i) for i in range(30)}  # candidate "29" is the unique best
        search = GeneticAlgorithmSearch(rng=random.Random(42))
        fitness = _FakeFitness(scores)

        result = search.search(candidates, _request(), fitness)

        assert result[0].strategy_id == "29"  # highest score ranked first

    def test_result_size_respects_max_candidates_cap(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(50))
        scores = {str(i): Decimal(i) for i in range(50)}
        search = GeneticAlgorithmSearch(rng=random.Random(3))
        fitness = _FakeFitness(scores)

        result = search.search(candidates, _request(max_candidates=5), fitness)

        assert len(result) <= 5


class TestCrossoverRecombinesRealLegsOnly:
    def test_compatible_parents_produce_a_recombined_child(self) -> None:
        """Two structurally compatible (same type, same leg count) parents
        with distinct strikes: the child's legs are drawn position-for-
        position from either parent, and for at least one seed that mix is
        genuinely new (not identical to either parent's full leg tuple)."""
        parent_a = _spread("A", 100, 200)
        parent_b = _spread("B", 150, 250)
        search = GeneticAlgorithmSearch(rng=random.Random(1))

        child = search._crossover(parent_a, parent_b)

        assert child.legs[0] in (parent_a.legs[0], parent_b.legs[0])
        assert child.legs[1] in (parent_a.legs[1], parent_b.legs[1])
        assert child.legs not in (parent_a.legs, parent_b.legs)
        assert child.strategy_id not in (parent_a.strategy_id, parent_b.strategy_id)

    def test_incompatible_parents_are_carried_forward_unchanged(self) -> None:
        """Different recognized_type/leg count can't be crossed without
        inventing a leg combination the generator never produced, so the
        first parent is returned as-is rather than a fabricated hybrid."""
        parent_a = _spread("A", 100, 200)
        parent_b = _strategy("B")  # single leg, different recognized_type
        search = GeneticAlgorithmSearch(rng=random.Random(2))

        child = search._crossover(parent_a, parent_b)

        assert child is parent_a

    def test_every_leg_in_every_returned_candidate_came_from_a_real_candidate(self) -> None:
        """Recombination never invents a strike -- every leg object
        returned, including on crossover children, is identical to (is,
        not just equal to) a leg carried by one of the original candidates."""
        candidates = tuple(_spread(str(i), 100 + i, 200 + i) for i in range(10))
        real_legs = {id(leg) for c in candidates for leg in c.legs}
        search = GeneticAlgorithmSearch(rng=random.Random(11))
        fitness = _FakeFitness({})

        result = search.search(candidates, _request(), fitness)

        assert all(id(leg) in real_legs for c in result for leg in c.legs)


class TestDeterminismWithSeededRng:
    def test_same_seed_produces_same_result(self) -> None:
        candidates = tuple(_strategy(str(i)) for i in range(15))
        scores = {str(i): Decimal(i % 7) for i in range(15)}

        result_a = GeneticAlgorithmSearch(rng=random.Random(99)).search(
            candidates, _request(), _FakeFitness(scores)
        )
        result_b = GeneticAlgorithmSearch(rng=random.Random(99)).search(
            candidates, _request(), _FakeFitness(scores)
        )

        assert [c.strategy_id for c in result_a] == [c.strategy_id for c in result_b]

    def test_fitness_is_not_recomputed_for_a_candidate_already_scored(self) -> None:
        """A population member (or child) already scored this run must not
        trigger a second real evaluation -- fitness.score() is the
        expensive part (a full engine evaluation in production)."""
        candidates = tuple(_strategy(str(i)) for i in range(3))  # small pool -> guaranteed repeats
        scores = {str(i): Decimal(i) for i in range(3)}
        search = GeneticAlgorithmSearch(rng=random.Random(5))
        fitness = _FakeFitness(scores)

        search.search(candidates, _request(), fitness)

        # At most one score() call per distinct candidate -- far fewer than
        # population_size * generations would need without caching.
        assert fitness.call_count <= len(candidates)
