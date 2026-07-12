"""Cache key helpers."""

from app.strategy_optimizer.models.request import OptimizationRequest


def build_cache_key(request: OptimizationRequest) -> str:
    """Build cache key for optimization."""
    prefs = request.preferences
    return (
        f"{request.calculation_context.exchange}:"
        f"{prefs.underlying}:"
        f"{prefs.expiry}:"
        f"{prefs.primary_objective.value}:"
        f"{prefs.search_algorithm.value}"
    )
