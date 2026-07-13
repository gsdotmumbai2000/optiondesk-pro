"""Live analytics services package."""

__all__ = [
    "CalculationDispatcher",
    "LiveAnalyticsService",
    "LiveAnalyticsServiceBundle",
    "LiveOptionChainService",
    "RefreshCoordinator",
    "SynchronizationService",
]


def __getattr__(name: str):
    if name == "CalculationDispatcher":
        from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher

        return CalculationDispatcher
    if name == "LiveAnalyticsService":
        from app.live.services.live_analytics_service import LiveAnalyticsService

        return LiveAnalyticsService
    if name == "LiveAnalyticsServiceBundle":
        from app.live.services.bundle import LiveAnalyticsServiceBundle

        return LiveAnalyticsServiceBundle
    if name == "LiveOptionChainService":
        from app.live.services.live_option_chain_service import LiveOptionChainService

        return LiveOptionChainService
    if name == "RefreshCoordinator":
        from app.live.refresh.refresh_coordinator import RefreshCoordinator

        return RefreshCoordinator
    if name == "SynchronizationService":
        from app.live.synchronization.sync_service import SynchronizationService

        return SynchronizationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
