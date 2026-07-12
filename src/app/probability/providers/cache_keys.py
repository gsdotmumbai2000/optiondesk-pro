"""Cache key helpers."""

from app.probability.models.request import ProbabilityAnalysisRequest


def build_cache_key(request: ProbabilityAnalysisRequest) -> str:
    """Build cache key for probability analytics."""
    return (
        f"{request.context.exchange}:"
        f"{request.context.underlying}:"
        f"{request.context.spot_price}:"
        f"{request.chain_analysis.atm_iv}"
    )
