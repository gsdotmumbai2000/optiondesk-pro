"""Dividend yield provider."""

from decimal import Decimal

from app.calculation.utilities.normalize_utils import normalize_interest_rate


class DividendProvider:
    """Supply dividend yield."""

    def __init__(self, *, dividend_yield: Decimal = Decimal("0")) -> None:
        """Initialize dividend yield."""
        self._dividend_yield = normalize_interest_rate(dividend_yield)

    def dividend_yield(self) -> Decimal:
        """Return dividend yield."""
        return self._dividend_yield
