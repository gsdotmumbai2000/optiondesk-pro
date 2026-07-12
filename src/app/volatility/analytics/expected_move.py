"""Expected move analytics."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext


def expected_move(
    spot: Decimal,
    implied_vol: Decimal,
    context: CalculationContext,
) -> tuple[Decimal, Decimal | None]:
    """Return expected move to expiry and one-day move."""
    tte = context.time_to_expiry
    if tte <= 0 or implied_vol <= 0:
        return Decimal("0"), Decimal("0")
    to_expiry = spot * implied_vol * tte.sqrt()
    one_day = spot * implied_vol / Decimal("15.8745")
    return to_expiry, one_day
