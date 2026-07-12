"""Margin optimization models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MarginReductionSuggestion:
    """Suggestion to reduce margin usage."""

    suggestion_id: str
    description: str
    estimated_reduction: Decimal
    priority: int


@dataclass(frozen=True, slots=True)
class MarginOptimizationResult:
    """Margin optimization framework output."""

    capital_efficiency_score: Decimal
    unused_capital: Decimal
    current_margin: Decimal
    optimized_margin_estimate: Decimal
    suggestions: tuple[MarginReductionSuggestion, ...]
