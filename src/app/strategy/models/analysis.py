"""Strategy analysis aggregate."""

from dataclasses import dataclass
from decimal import Decimal

from app.strategy.models.context import StrategyContext
from app.strategy.models.enums import StrategyType
from app.strategy.models.score import StrategyScore


@dataclass(frozen=True, slots=True)
class StrategyAnalysis:
    """Aggregated strategy analysis from engine results."""

    context: StrategyContext
    recognized_type: StrategyType
    probability_of_profit: Decimal
    expected_move: Decimal
    capital_efficiency: Decimal
    margin_utilization: Decimal
    liquidity_score: Decimal
    strategy_rating: Decimal
    score: StrategyScore
