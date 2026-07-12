"""Breakeven price detection."""

from decimal import Decimal

from app.payoff.models.result import PayoffCurve


def find_breakevens(curve: PayoffCurve) -> tuple[Decimal, ...]:
    """Find breakeven underlying prices where PnL crosses zero."""
    points = curve.points
    if len(points) < 2:
        return ()
    breakevens: list[Decimal] = []
    for left, right in zip(points, points[1:]):
        if left.pnl == 0:
            breakevens.append(left.underlying_price)
        if left.pnl * right.pnl < 0:
            span = right.underlying_price - left.underlying_price
            if span == 0:
                continue
            ratio = left.pnl / (left.pnl - right.pnl)
            breakevens.append(left.underlying_price + span * ratio)
    if points[-1].pnl == 0:
        breakevens.append(points[-1].underlying_price)
    return tuple(breakevens)
