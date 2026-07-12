"""Scoring models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RecommendationScores:
    """Composite scores for a recommendation."""

    confidence_score: Decimal
    impact_score: Decimal
    risk_score: Decimal
    capital_score: Decimal
    liquidity_score: Decimal
    priority_score: Decimal
