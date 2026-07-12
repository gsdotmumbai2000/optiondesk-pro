"""Normal distribution helpers for Black-Scholes."""

import math

_SQRT_2 = math.sqrt(2.0)
_SQRT_2PI = math.sqrt(2.0 * math.pi)
_INV_SQRT_2PI = 1.0 / _SQRT_2PI


def normal_pdf(x: float) -> float:
    """Return standard normal probability density at x."""
    return _INV_SQRT_2PI * math.exp(-0.5 * x * x)


def normal_cdf(x: float) -> float:
    """Return standard normal cumulative distribution at x."""
    return 0.5 * math.erfc(-x / _SQRT_2)
