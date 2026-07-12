"""Capital efficiency metrics."""

from decimal import Decimal

from app.payoff.models.result import PayoffResult


def capital_efficiency(
    payoff: PayoffResult,
    capital_required: Decimal,
) -> Decimal:
    """Compute capital efficiency as future value per capital."""
    if capital_required <= 0:
        return Decimal("0")
    return payoff.future_value / capital_required


def leverage_ratio(
    notional: Decimal,
    capital_required: Decimal,
) -> Decimal:
    """Compute leverage ratio."""
    if capital_required <= 0:
        return Decimal("0")
    return notional / capital_required
