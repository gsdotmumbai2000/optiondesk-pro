"""Placeholder search algorithms (framework only)."""

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest


class HeuristicSearch:
    """Heuristic search placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "heuristic"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        return candidates[: min(len(candidates), 100)]


class GeneticAlgorithmSearch:
    """Genetic algorithm placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "genetic"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        raise NotImplementedError("Genetic algorithm not yet implemented")


class ParticleSwarmSearch:
    """Particle swarm placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "particle_swarm"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        raise NotImplementedError("Particle swarm not yet implemented")


class SimulatedAnnealingSearch:
    """Simulated annealing placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "simulated_annealing"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        raise NotImplementedError("Simulated annealing not yet implemented")


class BranchAndBoundSearch:
    """Branch and bound placeholder."""

    @property
    def algorithm_id(self) -> str:
        return "branch_and_bound"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        raise NotImplementedError("Branch and bound not yet implemented")
