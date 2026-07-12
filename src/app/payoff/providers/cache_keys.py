"""Cache key helpers."""

from app.payoff.models.request import PayoffAnalysisRequest


def build_cache_key(request: PayoffAnalysisRequest) -> str:
    """Build cache key for payoff analytics."""
    leg_sig = ":".join(
        f"{leg.strike}:{leg.option_type.value}:{leg.quantity}" for leg in request.legs
    )
    return (
        f"{request.context.exchange}:"
        f"{request.context.underlying}:"
        f"{request.context.spot_price}:"
        f"{leg_sig}"
    )
