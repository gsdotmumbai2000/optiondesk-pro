"""Cache key helpers."""

from app.risk.models.request import RiskAnalysisRequest


def build_cache_key(request: RiskAnalysisRequest) -> str:
    """Build cache key for risk analytics."""
    leg_sig = ":".join(
        f"{leg.strike}:{leg.option_type.value}:{leg.quantity}" for leg in request.legs
    )
    return (
        f"{request.context.exchange}:"
        f"{request.context.underlying}:"
        f"{request.market_snapshot.snapshot_id}:"
        f"{leg_sig}"
    )
