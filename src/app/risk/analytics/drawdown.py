"""Maximum drawdown estimation."""

from decimal import Decimal

from app.payoff.models.result import PayoffResult


def maximum_drawdown(payoff: PayoffResult) -> Decimal:
    """Estimate maximum drawdown from payoff risk table."""
    if not payoff.risk_table.rows:
        if payoff.maximum_loss is not None:
            return abs(payoff.maximum_loss)
        return Decimal("0")
    worst = min(row.pnl for row in payoff.risk_table.rows)
    return abs(worst) if worst < 0 else Decimal("0")
