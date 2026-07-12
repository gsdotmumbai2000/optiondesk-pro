"""Candidate strategy models."""

from dataclasses import dataclass
from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.scoring import OptimizerScore


@dataclass(frozen=True, slots=True)
class GreeksSummary:
    """Greeks summary from engine results (no local calculation)."""

    net_delta: Decimal
    net_gamma: Decimal
    net_theta: Decimal
    net_vega: Decimal


@dataclass(frozen=True, slots=True)
class CandidateStrategy:
    """Evaluated candidate strategy."""

    evaluation: StrategyEvaluation
    score: OptimizerScore
    greeks_summary: GreeksSummary
    rank: int = 0
