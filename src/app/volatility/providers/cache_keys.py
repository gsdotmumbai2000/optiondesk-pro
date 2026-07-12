"""Cache key helpers."""

from app.volatility.models.request import VolatilityAnalysisRequest


def build_cache_key(request: VolatilityAnalysisRequest) -> str:
    """Build cache key for volatility analytics."""
    return (
        f"{request.context.exchange}:"
        f"{request.context.underlying}:"
        f"{request.market_snapshot.snapshot_id}:"
        f"{request.context.spot_price}"
    )
