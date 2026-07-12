"""User optimization preferences."""

from dataclasses import dataclass
from decimal import Decimal

from app.strategy_optimizer.models.enums import (
    MarketOutlook,
    OptimizationObjective,
    RankingSize,
    RiskPreference,
    SearchAlgorithmType,
)


@dataclass(frozen=True, slots=True)
class OptimizationPreferences:
    """User optimization preferences."""

    underlying: str
    expiry: str
    capital: Decimal
    market_outlook: MarketOutlook
    risk_preference: RiskPreference
    primary_objective: OptimizationObjective
    secondary_objectives: tuple[OptimizationObjective, ...] = ()
    ranking_size: RankingSize = RankingSize.TOP_25
    custom_rank_limit: int = 25
    search_algorithm: SearchAlgorithmType = SearchAlgorithmType.BRUTE_FORCE
    max_candidates: int = 1000
