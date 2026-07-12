"""Composite risk score."""

from decimal import Decimal


def risk_score(
    value_at_risk: Decimal,
    expected_shortfall: Decimal,
    portfolio_volatility: Decimal,
    concentration: Decimal,
) -> Decimal:
    """Compute composite risk score (0-100 scale)."""
    raw = (
        value_at_risk * Decimal("0.35")
        + expected_shortfall * Decimal("0.30")
        + portfolio_volatility * Decimal("100") * Decimal("0.20")
        + concentration * Decimal("100") * Decimal("0.15")
    )
    capped = min(raw, Decimal("100"))
    return capped if capped >= 0 else Decimal("0")
