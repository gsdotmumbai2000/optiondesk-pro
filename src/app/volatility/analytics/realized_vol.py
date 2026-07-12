"""Realized and historical volatility analytics."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.volatility.models.snapshots import HistoricalDataSnapshot
from app.volatility.models.volatility_result import HistoricalVolatility

TRADING_DAYS = Decimal("252")
SQRT_TRADING_DAYS = Decimal("15.8745")


def realized_volatility(
    historical: HistoricalDataSnapshot,
    context: CalculationContext,
) -> Decimal:
    """Compute realized volatility from historical returns."""
    if historical.returns:
        values = historical.returns
    elif len(historical.closes) >= 2:
        values = tuple(
            (historical.closes[idx] - historical.closes[idx - 1])
            / historical.closes[idx - 1]
            for idx in range(1, len(historical.closes))
            if historical.closes[idx - 1] != 0
        )
    else:
        values = ()
    if not values:
        if context.historical_volatility is not None and context.historical_volatility > 0:
            return context.historical_volatility
        return context.volatility
    mean = sum(values) / Decimal(len(values))
    variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
    if variance <= 0:
        return context.volatility
    return variance.sqrt() * SQRT_TRADING_DAYS


def historical_volatility(
    realized: Decimal,
    context: CalculationContext,
) -> HistoricalVolatility:
    """Build historical volatility bundle."""
    primary = context.historical_volatility or realized
    return HistoricalVolatility(
        primary=primary,
        short_term=realized,
        long_term=primary,
    )
