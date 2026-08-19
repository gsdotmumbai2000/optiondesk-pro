"""Real Simulated Annealing search: walks the candidate space using genuine
per-candidate fitness feedback (via CandidateFitnessEvaluator), unlike
BruteForceSearch/HeuristicSearch which have no fitness signal to work with
-- OptimizerEngine.optimize() runs search() before evaluation for those, but
this is the one algorithm that evaluates candidates as it goes.

Standard Metropolis-criterion SA for maximization: propose a neighbor,
accept it outright if it's better, or accept a worse one with probability
exp(delta / temperature) so the walk can escape local optima early (high
temperature) while converging as temperature cools. Neighbors are drawn
from the candidate pool CandidateGenerator produced (mostly same recognized
StrategyType, so moves are usually a small strike/width step; occasionally
a jump to a different structure, for exploration) -- not fabricated new
leg combinations, so every candidate this ever proposes is one the
generator already deemed a valid instrument.

Every candidate this returns gets evaluated a second time by
OptimizerEngine's own evaluate_batch() downstream (constraints/filter/score/
rank all need a fresh StrategyEvaluation, and search() only returns
Strategy objects) -- so the iteration budget and returned elite-set size
are both kept deliberately small. Without that, SA could easily cost *more*
real evaluations than BruteForceSearch evaluating the whole pool outright,
defeating the entire point of using a bounded search instead.
"""

import math
import random
from decimal import Decimal

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator

_INITIAL_TEMPERATURE = Decimal("100")
_COOLING_RATE = Decimal("0.95")
_MINIMUM_TEMPERATURE = Decimal("0.01")
_MAX_ITERATIONS = 60
_ELITE_SIZE = 30  # cap on returned candidates, independent of preferences.max_candidates
_SAME_TYPE_NEIGHBOR_PROBABILITY = 0.8


class SimulatedAnnealingSearch:
    """Simulated annealing over the generated candidate pool, guided by
    real engine-evaluated fitness."""

    def __init__(self, rng: random.Random | None = None) -> None:
        """`rng` is injectable for deterministic tests; production use gets
        a fresh, unseeded Random()."""
        self._rng = rng or random.Random()

    @property
    def algorithm_id(self) -> str:
        return "simulated_annealing"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy, ...]:
        if not candidates:
            return ()
        by_type = self._group_by_type(candidates)

        current, current_score = self._first_scored(candidates, fitness)
        if current is None:
            return ()  # every candidate failed evaluation -- nothing usable

        visited: dict[str, tuple[Strategy, Decimal]] = {current.strategy_id: (current, current_score)}

        temperature = _INITIAL_TEMPERATURE
        for _ in range(_MAX_ITERATIONS):
            if temperature <= _MINIMUM_TEMPERATURE:
                break
            neighbor = self._propose_neighbor(current, candidates, by_type)
            temperature *= _COOLING_RATE

            cached = visited.get(neighbor.strategy_id)
            neighbor_score = cached[1] if cached is not None else fitness.score(neighbor)
            if neighbor_score is None:
                continue
            visited[neighbor.strategy_id] = (neighbor, neighbor_score)

            if self._accept(neighbor_score, current_score, temperature):
                current, current_score = neighbor, neighbor_score

        ranked = sorted(visited.values(), key=lambda pair: pair[1], reverse=True)
        limit = min(request.preferences.max_candidates, _ELITE_SIZE)
        return tuple(strategy for strategy, _ in ranked[:limit])

    def _first_scored(
        self,
        candidates: tuple[Strategy, ...],
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy | None, Decimal]:
        """Find a usable starting point: the first candidate (in shuffled
        order) that evaluates successfully."""
        order = list(candidates)
        self._rng.shuffle(order)
        for candidate in order:
            score = fitness.score(candidate)
            if score is not None:
                return candidate, score
        return None, Decimal("0")

    def _propose_neighbor(
        self,
        current: Strategy,
        candidates: tuple[Strategy, ...],
        by_type: dict[object, tuple[Strategy, ...]],
    ) -> Strategy:
        same_type = tuple(
            c for c in by_type.get(current.metadata.recognized_type, ()) if c.strategy_id != current.strategy_id
        )
        if same_type and self._rng.random() < _SAME_TYPE_NEIGHBOR_PROBABILITY:
            return self._rng.choice(same_type)
        other = tuple(c for c in candidates if c.strategy_id != current.strategy_id)
        return self._rng.choice(other) if other else current

    def _accept(self, neighbor_score: Decimal, current_score: Decimal, temperature: Decimal) -> bool:
        if neighbor_score >= current_score:
            return True
        delta = float(neighbor_score - current_score)
        probability = math.exp(delta / float(temperature))
        return self._rng.random() < probability

    @staticmethod
    def _group_by_type(candidates: tuple[Strategy, ...]) -> dict[object, tuple[Strategy, ...]]:
        groups: dict[object, list[Strategy]] = {}
        for candidate in candidates:
            groups.setdefault(candidate.metadata.recognized_type, []).append(candidate)
        return {key: tuple(value) for key, value in groups.items()}
