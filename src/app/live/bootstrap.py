"""Enterprise live analytics bootstrap."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.calculation.bootstrap import CalculationProvider
from app.events.event_bus import EventBus
from app.live.analytics.publisher import AnalyticsPublisher
from app.live.cache.greeks_cache import LiveGreeksCache
from app.live.cache.option_cache import LiveOptionCache
from app.live.cache.portfolio_cache import LivePortfolioCache
from app.live.cache.risk_cache import LiveRiskCache
from app.live.calculations.active_strategy_adapter import ActiveStrategyAdapter
from app.live.calculations.context_builder import LiveContextBuilder
from app.live.calculations.market_query_adapter import LiveMarketQueryAdapter
from app.live.calculations.pipeline import LiveCalculationPipeline
from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher
from app.live.models.enums import RefreshMode
from app.live.option_chain.chain_manager import OptionChainManager
from app.live.refresh.refresh_coordinator import RefreshCoordinator
from app.live.services.bundle import LiveAnalyticsServiceBundle
from app.live.services.live_analytics_service import LiveAnalyticsService
from app.live.services.live_option_chain_service import LiveOptionChainService
from app.live.synchronization.sync_service import SynchronizationService
from app.market_data.services.market_data_service import MarketDataService
from app.strategy.providers.bundle_factory import build_engine_bundle

if TYPE_CHECKING:
    from app.application.cache.workspace_cache import WorkspaceCache
    from app.application.registry.engine_registry import EngineRegistry
    from app.application.session.session_manager import SessionManager


class LiveAnalyticsProvider:
    """Wire live option chain and analytics engine."""

    def __init__(
        self,
        event_bus: EventBus,
        market_data: MarketDataService,
        engines: EngineRegistry | Any,
        *,
        refresh_mode: RefreshMode = RefreshMode.MS_500,
        sessions: SessionManager | None = None,
        workspace_cache: WorkspaceCache | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._option_cache = LiveOptionCache()
        self._greeks_cache = LiveGreeksCache()
        self._risk_cache = LiveRiskCache()
        self._portfolio_cache = LivePortfolioCache()
        query_adapter = LiveMarketQueryAdapter(market_data, self._option_cache)
        calculation = self._build_calculation_provider(query_adapter, engines)
        chain_manager = OptionChainManager(self._option_cache, market_data=market_data)
        active_strategy = (
            ActiveStrategyAdapter(sessions, workspace_cache)
            if sessions is not None and workspace_cache is not None
            else None
        )
        context_builder = LiveContextBuilder(
            calculation.engine.contexts, chain_manager, active_strategy
        )
        pipeline = LiveCalculationPipeline(build_engine_bundle(event_bus), context_builder)
        chain_service = LiveOptionChainService(chain_manager, self._option_cache)
        dispatcher = CalculationDispatcher(max_workers=4)
        refresh = RefreshCoordinator(refresh_mode)
        sync = SynchronizationService()
        publisher = AnalyticsPublisher(event_bus)
        self.service = LiveAnalyticsService(
            chain_service,
            chain_manager,
            pipeline,
            dispatcher,
            refresh,
            sync,
            publisher,
            self._greeks_cache,
            self._risk_cache,
            self._portfolio_cache,
            context_builder,
        )
        self.bundle = LiveAnalyticsServiceBundle(
            option_chain=chain_service,
            analytics=self.service,
            dispatcher=dispatcher,
            refresh=refresh,
            sync=sync,
        )

    def start(self) -> None:
        """Subscribe to market data events."""
        self.service.subscribe_events(self._event_bus)

    def stop(self) -> None:
        """Stop background workers."""
        self.bundle.dispatcher.shutdown()
        self.bundle.refresh.stop()

    def _build_calculation_provider(
        self,
        query_adapter: LiveMarketQueryAdapter,
        engines: EngineRegistry | Any,
    ) -> CalculationProvider:
        master = engines.market_master
        return CalculationProvider.from_services(
            market_data_query=query_adapter,
            instrument_service=master.instrument_service,
            expiry_service=master.expiry_service,
            calendar_service=master.calendar_service,
            event_bus=self._event_bus,
        )
