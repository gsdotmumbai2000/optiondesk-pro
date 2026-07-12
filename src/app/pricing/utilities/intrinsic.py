"""Intrinsic value utilities."""

from decimal import Decimal

from app.pricing.models.enums import OptionType


def intrinsic_value(spot: Decimal, strike: Decimal, option_type: OptionType) -> Decimal:
    """Return undiscounted intrinsic value."""
    if option_type == OptionType.CALL:
        return max(spot - strike, Decimal("0"))
    return max(strike - spot, Decimal("0"))
