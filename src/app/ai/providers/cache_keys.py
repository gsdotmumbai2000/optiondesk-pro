"""Cache key helpers."""

from app.ai.models.request import RecommendationAnalysisRequest


def build_cache_key(request: RecommendationAnalysisRequest) -> str:
    """Build cache key for AI recommendations."""
    snap = (
        request.market_snapshot.snapshot_id
        if request.market_snapshot
        else "no-snapshot"
    )
    return (
        f"{request.session_id}:{snap}:"
        f"{request.portfolio_result.calculation_timestamp.isoformat()}"
    )
