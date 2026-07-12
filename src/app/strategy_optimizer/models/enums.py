"""Strategy optimizer enumerations."""

from enum import Enum


class OptimizerModelVersion(str, Enum):
    """Optimizer schema version."""

    V1 = "strategy-optimizer-v1"


class OptimizationObjective(str, Enum):
    """Supported optimization objectives."""

    MAX_POP = "MAX_POP"
    MAX_EXPECTED_RETURN = "MAX_EXPECTED_RETURN"
    MIN_RISK = "MIN_RISK"
    MIN_MARGIN = "MIN_MARGIN"
    MAX_THETA = "MAX_THETA"
    DELTA_NEUTRAL = "DELTA_NEUTRAL"
    MIN_VEGA = "MIN_VEGA"
    MAX_CAPITAL_EFFICIENCY = "MAX_CAPITAL_EFFICIENCY"
    MIN_DRAWDOWN = "MIN_DRAWDOWN"


class MarketOutlook(str, Enum):
    """User market outlook."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    VOLATILE = "VOLATILE"


class RiskPreference(str, Enum):
    """User risk preference."""

    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


class RankingSize(str, Enum):
    """Ranking output sizes."""

    TOP_10 = "TOP_10"
    TOP_25 = "TOP_25"
    TOP_50 = "TOP_50"
    CUSTOM = "CUSTOM"


class SearchAlgorithmType(str, Enum):
    """Search algorithm types."""

    BRUTE_FORCE = "BRUTE_FORCE"
    HEURISTIC = "HEURISTIC"
    GENETIC = "GENETIC"
    PARTICLE_SWARM = "PARTICLE_SWARM"
    SIMULATED_ANNEALING = "SIMULATED_ANNEALING"
    BRANCH_AND_BOUND = "BRANCH_AND_BOUND"
