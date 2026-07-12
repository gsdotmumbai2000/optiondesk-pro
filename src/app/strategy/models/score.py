"""Strategy scoring models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class StrategyScore:
    """Immutable strategy score breakdown."""

    risk_score: Decimal
    reward_score: Decimal
    capital_efficiency: Decimal
    liquidity_score: Decimal
    probability_score: Decimal
    volatility_score: Decimal
    overall_score: Decimal


@dataclass(frozen=True, slots=True)
class StrategyRecommendation:
    """Strategy recommendation from evaluation."""

    strategy_id: str
    recommendation: str
    confidence: Decimal
    rationale: str
