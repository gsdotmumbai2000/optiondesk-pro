"""Optimizer scoring models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OptimizerScore:
    """Optimizer score breakdown from engine outputs."""

    risk_score: Decimal
    reward_score: Decimal
    pop_score: Decimal
    liquidity_score: Decimal
    margin_score: Decimal
    theta_score: Decimal
    volatility_score: Decimal
    capital_efficiency: Decimal
    overall_score: Decimal
