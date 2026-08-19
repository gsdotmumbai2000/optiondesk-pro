"""Search algorithm registry."""

from app.strategy_optimizer.models.enums import SearchAlgorithmType
from app.strategy_optimizer.search.brute_force import BruteForceSearch
from app.strategy_optimizer.search.genetic import GeneticAlgorithmSearch
from app.strategy_optimizer.search.placeholders import (
    BranchAndBoundSearch,
    HeuristicSearch,
    ParticleSwarmSearch,
)
from app.strategy_optimizer.search.port import SearchAlgorithm
from app.strategy_optimizer.search.simulated_annealing import SimulatedAnnealingSearch


def resolve_search_algorithm(
    algorithm_type: SearchAlgorithmType,
) -> SearchAlgorithm:
    """Resolve search algorithm by type."""
    mapping: dict[SearchAlgorithmType, SearchAlgorithm] = {
        SearchAlgorithmType.BRUTE_FORCE: BruteForceSearch(),
        SearchAlgorithmType.HEURISTIC: HeuristicSearch(),
        SearchAlgorithmType.GENETIC: GeneticAlgorithmSearch(),
        SearchAlgorithmType.PARTICLE_SWARM: ParticleSwarmSearch(),
        SearchAlgorithmType.SIMULATED_ANNEALING: SimulatedAnnealingSearch(),
        SearchAlgorithmType.BRANCH_AND_BOUND: BranchAndBoundSearch(),
    }
    return mapping[algorithm_type]
