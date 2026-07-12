"""Optimization result."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.strategy_optimizer.models.candidate import GreeksSummary
from app.strategy_optimizer.models.enums import OptimizerModelVersion
from app.strategy_optimizer.models.candidate import CandidateStrategy


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """Immutable optimization output."""

    candidate_strategies: tuple[CandidateStrategy, ...]
    overall_score: Decimal
    expected_return: Decimal
    expected_risk: Decimal
    probability_of_profit: Decimal
    capital_required: Decimal
    margin_required: Decimal
    greeks_summary: GreeksSummary
    liquidity_score: Decimal
    recommendation: str
    ranking: tuple[str, ...]
    optimization_timestamp: datetime
    model_version: OptimizerModelVersion = OptimizerModelVersion.V1
