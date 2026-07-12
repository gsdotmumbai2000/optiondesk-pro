"""Ranking service."""

from app.strategy_optimizer.models.candidate import CandidateStrategy
from app.strategy_optimizer.models.preferences import OptimizationPreferences
from app.strategy_optimizer.ranking.ranker import StrategyRanker


class RankingService:
    """Rank candidate strategies."""

    def __init__(self, ranker: StrategyRanker | None = None) -> None:
        """Initialize ranking service."""
        self._ranker = ranker or StrategyRanker()

    def rank(
        self,
        candidates: tuple[CandidateStrategy, ...],
        preferences: OptimizationPreferences,
    ) -> tuple[CandidateStrategy, ...]:
        """Rank candidates by score."""
        return self._ranker.rank(candidates, preferences)
