"""IV percentile analytics."""

from decimal import Decimal

from app.volatility.models.volatility_result import HistoricalVolatility


def iv_percentile(
    implied_vol: Decimal,
    historical: HistoricalVolatility,
) -> Decimal:
    """Estimate IV percentile against historical volatility."""
    baseline = historical.primary or historical.long_term or implied_vol
    if baseline <= 0:
        return Decimal("50")
    ratio = implied_vol / baseline
    if ratio <= Decimal("0.8"):
        return Decimal("25")
    if ratio >= Decimal("1.2"):
        return Decimal("75")
    return Decimal("50")
