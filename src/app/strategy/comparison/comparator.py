"""Strategy comparison."""

from dataclasses import dataclass
from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation


@dataclass(frozen=True, slots=True)
class StrategyComparison:
    """Comparison of multiple strategy evaluations."""

    evaluations: tuple[StrategyEvaluation, ...]
    best_strategy_id: str
    worst_strategy_id: str
    ranking: tuple[str, ...]


def compare_two(
    left: StrategyEvaluation,
    right: StrategyEvaluation,
) -> StrategyComparison:
    """Compare two strategy evaluations."""
    return compare_many((left, right))


def compare_many(
    evaluations: tuple[StrategyEvaluation, ...],
) -> StrategyComparison:
    """Compare and rank multiple evaluations."""
    if not evaluations:
        return StrategyComparison(
            evaluations=(),
            best_strategy_id="",
            worst_strategy_id="",
            ranking=(),
        )
    ranked = sorted(
        evaluations,
        key=lambda e: e.analysis.score.overall_score,
        reverse=True,
    )
    ranking = tuple(e.strategy.strategy_id for e in ranked)
    return StrategyComparison(
        evaluations=evaluations,
        best_strategy_id=ranking[0],
        worst_strategy_id=ranking[-1],
        ranking=ranking,
    )


def rank_by_score(
    evaluations: tuple[StrategyEvaluation, ...],
) -> tuple[StrategyEvaluation, ...]:
    """Rank evaluations by overall score descending."""
    return tuple(
        sorted(
            evaluations,
            key=lambda e: e.analysis.score.overall_score,
            reverse=True,
        )
    )
