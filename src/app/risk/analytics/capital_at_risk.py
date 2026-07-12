"""Capital at risk estimation."""

from decimal import Decimal

from app.payoff.models.result import PayoffResult


def capital_at_risk(
    payoff: PayoffResult,
    value_at_risk: Decimal,
) -> Decimal:
    """Estimate capital at risk from VaR and max loss."""
    max_loss = abs(payoff.maximum_loss) if payoff.maximum_loss is not None else Decimal("0")
    return max(value_at_risk, max_loss)
