"""Payoff curve construction."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.analytics.expiry_payoff import total_expiry_pnl
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.result import PayoffCurve, PayoffCurvePoint

DEFAULT_SAMPLES = 61
DEFAULT_LOWER_FACTOR = Decimal("0.70")
DEFAULT_UPPER_FACTOR = Decimal("1.30")


def price_bounds(
    context: CalculationContext,
    legs: tuple[StrategyLeg, ...],
) -> tuple[Decimal, Decimal]:
    spot = context.spot_price
    strikes = [leg.strike for leg in legs if leg.strike > 0]
    if strikes:
        low = min(min(strikes), spot) * DEFAULT_LOWER_FACTOR
        high = max(max(strikes), spot) * DEFAULT_UPPER_FACTOR
        return low, high
    return spot * DEFAULT_LOWER_FACTOR, spot * DEFAULT_UPPER_FACTOR


def sample_prices(
    low: Decimal,
    high: Decimal,
    samples: int,
    legs: tuple[StrategyLeg, ...],
) -> list[Decimal]:
    """Return sorted sample prices: an even grid, plus each leg's exact
    strike (when in range) so payoff kinks are never smoothed over by
    sparse sampling -- an evenly-spaced grid alone can land zero points
    inside a narrow strike gap on a wide auto-scaled price range, which
    visibly distorts a spline-rendered curve near that strike."""
    step = (high - low) / Decimal(samples - 1)
    grid = {low + step * Decimal(idx) for idx in range(samples)}
    strikes = {leg.strike for leg in legs if low <= leg.strike <= high}
    return sorted(grid | strikes)


def build_payoff_curve(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    *,
    samples: int = DEFAULT_SAMPLES,
) -> PayoffCurve:
    """Build expiry payoff curve across a price range."""
    if not legs or samples < 2:
        return PayoffCurve()
    low, high = price_bounds(context, legs)
    if high <= low:
        high = low + context.tick_size
    points = tuple(
        PayoffCurvePoint(underlying_price=price, pnl=total_expiry_pnl(price, legs))
        for price in sample_prices(low, high, samples, legs)
    )
    return PayoffCurve(points=points)
