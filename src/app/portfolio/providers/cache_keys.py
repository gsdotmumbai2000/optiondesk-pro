"""Cache key helpers."""

from app.portfolio.models.request import PortfolioAnalysisRequest


def build_cache_key(request: PortfolioAnalysisRequest) -> str:
    """Build cache key for portfolio analytics."""
    trade_sig = ":".join(
        f"{t.symbol}:{t.side}:{t.quantity}" for t in request.trade_executions
    )
    return f"{request.portfolio_id}:{trade_sig}"
