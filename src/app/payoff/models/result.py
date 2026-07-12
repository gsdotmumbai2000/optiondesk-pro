"""Payoff analysis result models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.payoff.models.enums import PayoffModelVersion


@dataclass(frozen=True, slots=True)
class PayoffCurvePoint:
    """Single point on a payoff curve."""

    underlying_price: Decimal
    pnl: Decimal


@dataclass(frozen=True, slots=True)
class PayoffCurve:
    """Expiry payoff curve across underlying prices."""

    points: tuple[PayoffCurvePoint, ...] = ()


@dataclass(frozen=True, slots=True)
class PayoffRiskRow:
    """Risk table row for scenario analysis."""

    underlying_price: Decimal
    pnl: Decimal
    probability: Decimal | None = None


@dataclass(frozen=True, slots=True)
class PayoffRiskTable:
    """Tabular payoff risk scenarios."""

    rows: tuple[PayoffRiskRow, ...] = ()


@dataclass(frozen=True, slots=True)
class PayoffResult:
    """Immutable payoff analytics output."""

    current_pnl: Decimal
    expiry_pnl: Decimal
    future_value: Decimal
    maximum_gain: Decimal | None
    maximum_loss: Decimal | None
    risk_reward_ratio: Decimal | None
    breakevens: tuple[Decimal, ...]
    payoff_curve: PayoffCurve
    risk_table: PayoffRiskTable
    probability_weighted_pnl: Decimal | None
    calculation_timestamp: datetime
    model_version: PayoffModelVersion = PayoffModelVersion.V1
