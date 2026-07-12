"""Payoff risk table construction."""

from decimal import Decimal

from app.payoff.models.result import PayoffCurve, PayoffRiskRow, PayoffRiskTable


def build_risk_table(curve: PayoffCurve) -> PayoffRiskTable:
    """Build risk table rows from payoff curve points."""
    if not curve.points:
        return PayoffRiskTable()
    total = Decimal(len(curve.points))
    rows = tuple(
        PayoffRiskRow(
            underlying_price=point.underlying_price,
            pnl=point.pnl,
            probability=Decimal("1") / total,
        )
        for point in curve.points
    )
    return PayoffRiskTable(rows=rows)


def curve_extrema(curve: PayoffCurve) -> tuple[Decimal | None, Decimal | None]:
    """Return maximum gain and maximum loss from a payoff curve."""
    if not curve.points:
        return None, None
    pnls = [point.pnl for point in curve.points]
    max_gain = max(pnls)
    max_loss = min(pnls)
    return (
        max_gain if max_gain > 0 else None,
        max_loss if max_loss < 0 else None,
    )
