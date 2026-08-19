"""Placeholder search algorithms (framework only).

SimulatedAnnealingSearch has moved to search/simulated_annealing.py and
GeneticAlgorithmSearch to search/genetic.py -- real implementations, not
placeholders.
"""

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator


class HeuristicSearch:
    """Heuristic search placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "heuristic"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy, ...]:
        return candidates[: min(len(candidates), 100)]


class ParticleSwarmSearch:
    """Particle swarm placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "particle_swarm"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy, ...]:
        raise NotImplementedError("Particle swarm not yet implemented")


class BranchAndBoundSearch:
    """Branch and bound placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "branch_and_bound"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy, ...]:
        raise NotImplementedError("Branch and bound not yet implemented")
