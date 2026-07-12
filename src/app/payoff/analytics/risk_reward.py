"""Risk-reward analytics."""

from decimal import Decimal


def risk_reward_ratio(
    maximum_gain: Decimal | None,
    maximum_loss: Decimal | None,
) -> Decimal | None:
    """Compute risk-reward ratio from payoff extrema."""
    if maximum_gain is None or maximum_loss is None:
        return None
    if maximum_loss >= 0:
        return None
    if maximum_gain <= 0:
        return Decimal("0")
    return maximum_gain / abs(maximum_loss)
