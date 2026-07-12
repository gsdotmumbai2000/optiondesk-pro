"""Enterprise Option Chain Analytics Engine."""

__all__ = [
    "ChainMarketSnapshot",
    "OptionChainAnalysis",
    "OptionChainAnalyticsService",
    "OptionChainProvider",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "ChainMarketSnapshot":
        from app.option_chain.models.market_snapshot import ChainMarketSnapshot

        return ChainMarketSnapshot
    if name == "OptionChainAnalysis":
        from app.option_chain.models.analysis import OptionChainAnalysis

        return OptionChainAnalysis
    if name == "OptionChainAnalyticsService":
        from app.option_chain.services.analytics_service import OptionChainAnalyticsService

        return OptionChainAnalyticsService
    if name == "OptionChainProvider":
        from app.option_chain.bootstrap import OptionChainProvider

        return OptionChainProvider
    raise AttributeError(name)
