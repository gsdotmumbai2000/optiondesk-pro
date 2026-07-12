"""Strategy ranking."""

from app.strategy_optimizer.models.candidate import CandidateStrategy
from app.strategy_optimizer.models.enums import RankingSize
from app.strategy_optimizer.models.preferences import OptimizationPreferences


class StrategyRanker:
    """Rank candidate strategies by overall score."""

    def rank(
        self,
        candidates: tuple[CandidateStrategy, ...],
        preferences: OptimizationPreferences,
    ) -> tuple[CandidateStrategy, ...]:
        """Rank and limit candidates."""
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.score.overall_score,
            reverse=True,
        )
        limit = self._resolve_limit(preferences)
        ranked = tuple(
            CandidateStrategy(
                evaluation=c.evaluation,
                score=c.score,
                greeks_summary=c.greeks_summary,
                rank=idx + 1,
            )
            for idx, c in enumerate(sorted_candidates[:limit])
        )
        return ranked

    def _resolve_limit(self, preferences: OptimizationPreferences) -> int:
        mapping = {
            RankingSize.TOP_10: 10,
            RankingSize.TOP_25: 25,
            RankingSize.TOP_50: 50,
            RankingSize.CUSTOM: preferences.custom_rank_limit,
        }
        return mapping.get(preferences.ranking_size, 25)
