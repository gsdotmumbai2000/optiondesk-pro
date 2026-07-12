"""Margin fields adapter from margin engine."""

from decimal import Decimal

from app.margin.models.result import MarginResult


class MarginAdapter:
    """Extract margin fields from margin engine output."""

    def extract(
        self,
        margin: MarginResult | None,
        cash_available: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Return used margin and available margin."""
        if margin is None:
            return Decimal("0"), cash_available
        used = margin.total_margin
        available = margin.available_margin
        return used, available
