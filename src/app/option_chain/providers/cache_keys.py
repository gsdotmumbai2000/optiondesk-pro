"""Cache key helpers."""

from app.option_chain.models.request import OptionChainAnalysisRequest


def build_cache_key(request: OptionChainAnalysisRequest) -> str:
    """Build cache key for option chain analytics."""
    return (
        f"{request.context.exchange}:"
        f"{request.context.underlying}:"
        f"{request.market_snapshot.snapshot_id}:"
        f"{len(request.option_chain.strikes)}"
    )
