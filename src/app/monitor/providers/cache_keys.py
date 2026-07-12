"""Cache key helpers."""

from app.monitor.models.request import MonitorAnalysisRequest


def build_cache_key(request: MonitorAnalysisRequest) -> str:
    """Build cache key for monitor analytics."""
    snap = (
        request.market_snapshot.snapshot_id
        if request.market_snapshot
        else "no-snapshot"
    )
    return f"{request.session_id}:{snap}:{len(request.portfolio_result.open_positions)}"
