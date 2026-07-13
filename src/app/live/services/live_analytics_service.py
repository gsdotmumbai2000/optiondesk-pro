"""Live analytics orchestration service."""

from app.live.analytics.publisher import AnalyticsPublisher
from app.live.cache.greeks_cache import LiveGreeksCache
from app.live.cache.portfolio_cache import LivePortfolioCache
from app.live.cache.risk_cache import LiveRiskCache
from app.live.calculations.pipeline import LiveCalculationPipeline
from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.chain_key import ChainKey
from app.live.models.enums import RefreshMode
from app.live.option_chain.chain_manager import OptionChainManager
from app.live.refresh.refresh_coordinator import RefreshCoordinator
from app.live.services.live_option_chain_service import LiveOptionChainService
from app.live.synchronization.sync_service import SynchronizationService
from app.live.validation.freshness_validator import FreshnessValidator
from app.market_data.events import OptionUpdatedEvent, PriceUpdatedEvent, QuoteUpdatedEvent
from app.market_data.models.tick import TickSnapshot


class LiveAnalyticsService:
    """Coordinate live chain updates and analytics refresh."""

    def __init__(
        self,
        chain_service: LiveOptionChainService,
        chain_manager: OptionChainManager,
        pipeline: LiveCalculationPipeline,
        dispatcher: CalculationDispatcher,
        refresh: RefreshCoordinator,
        sync: SynchronizationService,
        publisher: AnalyticsPublisher,
        greeks_cache: LiveGreeksCache,
        risk_cache: LiveRiskCache,
        portfolio_cache: LivePortfolioCache,
        *,
        freshness: FreshnessValidator | None = None,
    ) -> None:
        self._chain_service = chain_service
        self._chain_manager = chain_manager
        self._pipeline = pipeline
        self._dispatcher = dispatcher
        self._refresh = refresh
        self._sync = sync
        self._publisher = publisher
        self._greeks_cache = greeks_cache
        self._risk_cache = risk_cache
        self._portfolio_cache = portfolio_cache
        self._freshness = freshness or FreshnessValidator()

    def set_refresh_mode(self, mode: RefreshMode) -> None:
        self._refresh.set_mode(mode)

    def refresh_mode(self) -> RefreshMode:
        return self._refresh.mode

    def get_analytics(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveAnalyticsSnapshot | None:
        return self._risk_cache.get(ChainKey(underlying, exchange, expiry_date))

    def get_chain(self, underlying: str, exchange: str, expiry_date: str):
        return self._chain_service.get_chain(underlying, exchange, expiry_date)

    def request_refresh(self, underlying: str, exchange: str, expiry_date: str) -> None:
        key = ChainKey(underlying, exchange, expiry_date)
        self._refresh.request_manual_refresh(key)
        self._schedule(key)

    def on_market_event(self, event: object) -> None:
        tick = self._extract_tick(event)
        if tick is None:
            return
        chain = self._chain_service.on_tick(tick)
        if chain is None:
            return
        key = ChainKey(chain.underlying, chain.exchange, chain.expiry_date)
        self._publisher.publish_chain(key, chain)
        if self._refresh.should_refresh(key):
            self._schedule(key)

    def _schedule(self, key: ChainKey) -> None:
        self._dispatcher.submit(key, self._calculate)

    def _calculate(self, key: ChainKey) -> None:
        snapshot = self._pipeline.run(key)
        self._freshness.validate(snapshot)
        if snapshot.greeks is not None:
            self._greeks_cache.put(key, snapshot.greeks)
        self._risk_cache.put(key, snapshot)
        if snapshot.portfolio_greeks is not None:
            self._portfolio_cache.put(key.cache_key(), snapshot.portfolio_greeks)
        if snapshot.position_greeks is not None:
            self._portfolio_cache.put_position(key, snapshot.position_greeks)
        self._publisher.publish_snapshot(key, snapshot)
        self._sync.notify(key)

    @staticmethod
    def _extract_tick(event: object) -> TickSnapshot | None:
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            return None
        tick_data = payload.get("tick")
        if not isinstance(tick_data, dict):
            return None
        return TickSnapshot.model_validate(tick_data)

    def subscribe_events(self, event_bus) -> None:
        if event_bus is None:
            return
        event_bus.subscribe(PriceUpdatedEvent, self.on_market_event)
        event_bus.subscribe(QuoteUpdatedEvent, self.on_market_event)
        event_bus.subscribe(OptionUpdatedEvent, self.on_market_event)
