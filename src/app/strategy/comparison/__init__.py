"""Strategy comparison package."""

from app.strategy.comparison.comparator import (
    StrategyComparison,
    compare_many,
    compare_two,
    rank_by_score,
)

__all__ = ["StrategyComparison", "compare_many", "compare_two", "rank_by_score"]
