"""Normalization utility functions."""

from decimal import Decimal

from app.calculation.exceptions import InvalidContextException


def normalize_price(value: Decimal) -> Decimal:
    """Normalize a price value."""
    if value < 0:
        raise InvalidContextException("price cannot be negative")
    return value.quantize(Decimal("0.0001"))


def normalize_volatility(value: Decimal) -> Decimal:
    """Normalize volatility to decimal form."""
    if value < 0:
        raise InvalidContextException("volatility cannot be negative")
    if value > 5:
        return (value / Decimal("100")).quantize(Decimal("0.0001"))
    return value.quantize(Decimal("0.0001"))


def normalize_interest_rate(value: Decimal) -> Decimal:
    """Normalize interest rate to decimal form."""
    if value < 0:
        raise InvalidContextException("interest rate cannot be negative")
    if value > 1:
        return (value / Decimal("100")).quantize(Decimal("0.0001"))
    return value.quantize(Decimal("0.0001"))
