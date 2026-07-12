"""Cache key helpers."""

from app.strategy.models.request import StrategyEvaluationRequest


def build_cache_key(request: StrategyEvaluationRequest) -> str:
    """Build cache key for strategy evaluation."""
    leg_sig = ":".join(leg.leg_id for leg in request.legs)
    return (
        f"{request.calculation_context.exchange}:"
        f"{request.calculation_context.underlying}:"
        f"{request.strategy.strategy_id}:"
        f"{leg_sig}"
    )
