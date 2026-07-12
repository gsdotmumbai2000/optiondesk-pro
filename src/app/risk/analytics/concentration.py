"""Portfolio concentration metric."""

from decimal import Decimal

from app.payoff.models.legs import StrategyLeg


def portfolio_concentration(legs: tuple[StrategyLeg, ...]) -> Decimal:
    """Compute Herfindahl-style concentration across legs."""
    if not legs:
        return Decimal("0")
    notionals: list[Decimal] = []
    for leg in legs:
        n = abs(Decimal(leg.quantity) * Decimal(leg.multiplier) * leg.premium)
        notionals.append(n)
    total = sum(notionals)
    if total == 0:
        return Decimal("1")
    weights = [(n / total) for n in notionals]
    hhi = sum(w * w for w in weights)
    return hhi
