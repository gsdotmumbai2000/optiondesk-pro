"""Live analytics service bundle."""

from dataclasses import dataclass

from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher
from app.live.refresh.refresh_coordinator import RefreshCoordinator
from app.live.services.live_analytics_service import LiveAnalyticsService
from app.live.services.live_option_chain_service import LiveOptionChainService
from app.live.synchronization.sync_service import SynchronizationService


@dataclass(frozen=True, slots=True)
class LiveAnalyticsServiceBundle:
    """Enterprise live analytics services."""

    option_chain: LiveOptionChainService
    analytics: LiveAnalyticsService
    dispatcher: CalculationDispatcher
    refresh: RefreshCoordinator
    sync: SynchronizationService
