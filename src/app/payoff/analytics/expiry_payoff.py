"""Expiry payoff analytics."""

from decimal import Decimal

from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType
from app.pricing.utilities.intrinsic import intrinsic_value


def leg_expiry_pnl(spot: Decimal, leg: StrategyLeg) -> Decimal:
    """Return expiry PnL for a single leg at the given spot."""
    intrinsic = intrinsic_value(spot, leg.strike, leg.option_type)
    scale = Decimal(leg.quantity) * Decimal(leg.multiplier)
    return scale * intrinsic - scale * leg.premium


def total_expiry_pnl(spot: Decimal, legs: tuple[StrategyLeg, ...]) -> Decimal:
    """Return aggregate expiry PnL across all legs."""
    return sum((leg_expiry_pnl(spot, leg) for leg in legs), Decimal("0"))


def leg_intrinsic_exposure(leg: StrategyLeg) -> Decimal:
    """Return signed intrinsic exposure multiplier for risk heuristics."""
    sign = Decimal("1") if leg.option_type == OptionType.CALL else Decimal("-1")
    return Decimal(leg.quantity) * Decimal(leg.multiplier) * sign
