"""Decimal conversion helpers for pricing."""

from decimal import Decimal


def to_float(value: Decimal) -> float:
    """Convert decimal to float for numeric kernels."""
    return float(value)


def to_decimal(value: float, *, places: str = "0.0001") -> Decimal:
    """Convert float kernel output to quantized decimal."""
    return Decimal(str(value)).quantize(Decimal(places))
