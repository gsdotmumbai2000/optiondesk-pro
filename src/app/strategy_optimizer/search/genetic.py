"""Real Genetic Algorithm search: evolves the candidate pool via tournament
selection, structural crossover, and pool-based mutation, guided by real
per-candidate fitness feedback (via CandidateFitnessEvaluator) -- the same
constraint SimulatedAnnealingSearch operates under: every leg placed into an
offspring strategy is one already carried by a real, generator-produced
candidate, so recombination never invents a strike/premium/expiry the
generator hasn't already deemed a valid instrument. Crossover therefore only
combines two parents of the same recognized_type and leg count (structurally
compatible, so legs line up position-for-position); parents that don't match
are carried forward unchanged rather than forced into an invalid pairing.

Evaluation budget is bounded the same way SA's is: OptimizerEngine's own
evaluate_batch() re-evaluates everything this returns, so keeping population
size and generation count small matters -- otherwise a "bounded" search
algorithm would cost more real evaluations than BruteForceSearch evaluating
the whole pool outright.
"""

import random
from dataclasses import replace
from decimal import Decimal

from app.strategy.models.strategy import Strategy
from app.strategy.recognition.recognizer import recognize_strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator
from app.utils.uuid_helper import generate_uuid

_POPULATION_SIZE = 30
_GENERATIONS = 5
_ELITE_SIZE = 2
_TOURNAMENT_SIZE = 3
_MUTATION_RATE = 0.2
_RETURN_LIMIT = 30  # cap on returned candidates, independent of preferences.max_candidates


class GeneticAlgorithmSearch:
    """Genetic algorithm over the generated candidate pool, guided by real
    engine-evaluated fitness."""

    def __init__(self, rng: random.Random | None = None) -> None:
        """`rng` is injectable for deterministic tests; production use gets
        a fresh, unseeded Random()."""
        self._rng = rng or random.Random()

    @property
    def algorithm_id(self) -> str:
        return "genetic"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy, ...]:
        if not candidates:
            return ()

        scored: dict[str, tuple[Strategy, Decimal]] = {}
        population = self._initial_population(candidates)
        for strategy in population:
            self._score(strategy, fitness, scored)

        for _ in range(_GENERATIONS):
            ranked = self._ranked_alive(population, scored)
            if not ranked:
                break
            children: list[Strategy] = [strategy for strategy, _ in ranked[:_ELITE_SIZE]]
            while len(children) < len(population):
                parent_a = self._tournament_select(ranked)
                parent_b = self._tournament_select(ranked)
                child = self._crossover(parent_a, parent_b)
                if self._rng.random() < _MUTATION_RATE:
                    child = self._rng.choice(candidates)
                if child.strategy_id not in scored:
                    self._score(child, fitness, scored)
                children.append(child)
            population = children

        ranked = self._ranked_alive(population, scored)
        limit = min(request.preferences.max_candidates, _RETURN_LIMIT)
        return tuple(strategy for strategy, _ in ranked[:limit])

    def _initial_population(self, candidates: tuple[Strategy, ...]) -> list[Strategy]:
        pool = list(candidates)
        self._rng.shuffle(pool)
        return pool[:_POPULATION_SIZE]

    def _score(
        self,
        strategy: Strategy,
        fitness: CandidateFitnessEvaluator,
        scored: dict[str, tuple[Strategy, Decimal]],
    ) -> None:
        score = fitness.score(strategy)
        if score is not None:
            scored[strategy.strategy_id] = (strategy, score)

    def _ranked_alive(
        self,
        population: list[Strategy],
        scored: dict[str, tuple[Strategy, Decimal]],
    ) -> list[tuple[Strategy, Decimal]]:
        """Population members that failed evaluation (score is None) are
        dropped rather than kept as unrankable dead weight."""
        pairs = [scored[s.strategy_id] for s in population if s.strategy_id in scored]
        pairs.sort(key=lambda pair: pair[1], reverse=True)
        return pairs

    def _tournament_select(self, ranked: list[tuple[Strategy, Decimal]]) -> Strategy:
        size = min(_TOURNAMENT_SIZE, len(ranked))
        contenders = [ranked[self._rng.randrange(len(ranked))] for _ in range(size)]
        contenders.sort(key=lambda pair: pair[1], reverse=True)
        return contenders[0][0]

    def _crossover(self, parent_a: Strategy, parent_b: Strategy) -> Strategy:
        """Position-for-position leg crossover between two structurally
        compatible parents (same recognized type, same leg count) -- every
        leg in the child is one already carried by a real candidate, just
        recombined. Structurally incompatible parents can't be crossed
        without inventing a leg combination the generator never produced,
        so one parent is carried forward unchanged instead."""
        if (
            parent_a.metadata.recognized_type != parent_b.metadata.recognized_type
            or len(parent_a.legs) != len(parent_b.legs)
            or not parent_a.legs
        ):
            return parent_a
        legs = tuple(
            leg_a if self._rng.random() < 0.5 else leg_b
            for leg_a, leg_b in zip(parent_a.legs, parent_b.legs)
        )
        if legs == parent_a.legs:
            return parent_a
        if legs == parent_b.legs:
            return parent_b
        metadata = replace(
            parent_a.metadata,
            strategy_id=generate_uuid(),
            name=f"{parent_a.metadata.name} x {parent_b.metadata.name}",
            recognized_type=recognize_strategy(legs),
        )
        return Strategy(metadata=metadata, legs=legs)
