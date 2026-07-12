"""Cache key helpers."""

from app.backtesting.models.request import BacktestRequest


def build_cache_key(request: BacktestRequest) -> str:
    """Build cache key for backtest."""
    return (
        f"{request.market_data.exchange}:"
        f"{request.market_data.underlying}:"
        f"{request.strategy.strategy_id}:"
        f"{request.parameters.initial_capital}"
    )
