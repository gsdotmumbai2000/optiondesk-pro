"""Cache key helpers."""

from app.margin.models.request import MarginAnalysisRequest


def build_cache_key(request: MarginAnalysisRequest) -> str:
    """Build cache key for margin analytics."""
    leg_sig = ":".join(
        f"{leg.strike}:{leg.option_type.value}:{leg.quantity}" for leg in request.legs
    )
    broker = request.broker_response.broker_id if request.broker_response else "est"
    return (
        f"{request.context.exchange}:"
        f"{request.context.underlying}:"
        f"{broker}:"
        f"{leg_sig}"
    )
