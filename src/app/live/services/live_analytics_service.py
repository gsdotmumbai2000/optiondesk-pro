"""Live analytics orchestration service."""

import time

from app.live.analytics.publisher import AnalyticsPublisher
from app.live.cache.greeks_cache import LiveGreeksCache
from app.live.cache.portfolio_cache import LivePortfolioCache
from app.live.cache.risk_cache import LiveRiskCache
from app.live.calculations.context_builder import LiveContextBuilder
from app.live.calculations.evaluation_context import EvaluationContext
from app.live.calculations.pipeline import LiveCalculationPipeline
from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher
from app.live.exceptions import LiveAnalyticsException
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.chain_key import ChainKey
from app.live.models.enums import RefreshMode
from app.live.option_chain.chain_manager import OptionChainManager
from app.live.refresh.refresh_coordinator import RefreshCoordinator
from app.live.services.live_option_chain_service import LiveOptionChainService
from app.live.synchronization.sync_service import SynchronizationService
from app.live.validation.freshness_validator import FreshnessValidator
from app.logging.logging_manager import get_logger
from app.market_data.events import OptionUpdatedEvent, PriceUpdatedEvent, QuoteUpdatedEvent
from app.market_data.models.tick import TickSnapshot

logger = get_logger(__name__)

# publish_chain() model_dump()s the whole chain (up to dozens of legs) and
# fans out to the UI, which does a full table + chart rebuild on the main
# thread -- gating that on every single tick (option ticks alone can arrive
# tens of times a second) backed up the UI thread badly enough to make the
# app appear frozen. Deliberately a separate throttle from `self._refresh`
# (which gates the heavier portfolio/risk/margin recalculation below): the
# two serve different consumers and must not share one clock, or one would
# silently steal the other's refresh slot.
_CHAIN_PUBLISH_INTERVAL_SECONDS = 0.5


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
        context_builder: LiveContextBuilder | None = None,
        *,
        freshness: FreshnessValidator | None = None,
    ) -> None:
        self._chain_service = chain_service
        self._chain_manager = chain_manager
        self._pipeline = pipeline
        self._context_builder = context_builder
        self._dispatcher = dispatcher
        self._refresh = refresh
        self._sync = sync
        self._publisher = publisher
        self._greeks_cache = greeks_cache
        self._risk_cache = risk_cache
        self._portfolio_cache = portfolio_cache
        self._freshness = freshness or FreshnessValidator()
        self._chain_published_at: dict[str, float] = {}

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

    def refresh_and_get_analytics(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveAnalyticsSnapshot | None:
        """Synchronously recompute and return analytics for a chain key, for
        on-demand callers (e.g. a UI "Evaluate" action) that need the result
        immediately rather than racing request_refresh()'s background
        dispatcher submission. Returns None when the chain hasn't been
        populated yet (e.g. never subscribed this session) or the
        calculation otherwise fails -- callers should treat that as "no
        result available", not as an error."""
        key = ChainKey(underlying, exchange, expiry_date)
        try:
            snapshot = self._pipeline.run(key)
            self._finalize(key, snapshot)
        except LiveAnalyticsException as error:
            logger.warning(
                "On-demand analytics refresh failed for {key}: {error}",
                key=key.cache_key(),
                error=error,
            )
            return None
        self._publisher.publish_snapshot(key, snapshot)
        self._sync.notify(key)
        return snapshot

    def build_evaluation_context(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> EvaluationContext | None:
        """Build the raw context bundle (CalculationContext, reference
        contract, chain snapshot, and market/volatility/historical
        snapshots) other callers need to construct their own evaluation
        requests (e.g. OptimizationRequest) -- the same pieces the live
        pipeline builds for a tick, just returned raw instead of fed
        straight into the frozen engines. Returns None when no
        context_builder was configured or the chain hasn't been populated
        yet (e.g. never subscribed this session)."""
        if self._context_builder is None:
            return None
        key = ChainKey(underlying, exchange, expiry_date)
        try:
            ctx = self._context_builder.build_context(key)
            contract = self._context_builder.build_contract(key, ctx)
            option_chain = self._context_builder.build_option_chain(key)
            market_snapshot = self._context_builder.build_market_snapshot(key, ctx)
            chain_market_snapshot = self._context_builder.build_chain_market_snapshot(key, ctx)
            volatility_market_snapshot = self._context_builder.build_volatility_snapshot(key, ctx)
            historical_data = self._context_builder.build_historical_snapshot(key)
        except ValueError as error:
            logger.warning(
                "Evaluation context unavailable for {key}: {error}",
                key=key.cache_key(),
                error=error,
            )
            return None
        return EvaluationContext(
            calculation_context=ctx,
            option_contract=contract,
            option_chain=option_chain,
            market_snapshot=market_snapshot,
            chain_market_snapshot=chain_market_snapshot,
            volatility_market_snapshot=volatility_market_snapshot,
            historical_data=historical_data,
        )

    def on_market_event(self, event: object) -> None:
        tick = self._extract_tick(event)
        if tick is None:
            return
        chain = self._chain_service.on_tick(tick)
        if chain is None:
            return
        key = ChainKey(chain.underlying, chain.exchange, chain.expiry_date)
        if self._should_publish_chain(key):
            self._publisher.publish_chain(key, chain)
        if self._refresh.should_refresh(key):
            self._schedule(key)

    def _should_publish_chain(self, key: ChainKey) -> bool:
        cache_key = key.cache_key()
        now = time.monotonic()
        last = self._chain_published_at.get(cache_key, 0.0)
        if now - last < _CHAIN_PUBLISH_INTERVAL_SECONDS:
            return False
        self._chain_published_at[cache_key] = now
        return True

    def _schedule(self, key: ChainKey) -> None:
        self._dispatcher.submit(key, self._calculate)

    def _calculate(self, key: ChainKey) -> None:
        snapshot = self._pipeline.run(key)
        self._finalize(key, snapshot)
        self._publisher.publish_snapshot(key, snapshot)
        self._sync.notify(key)

    def _finalize(self, key: ChainKey, snapshot: LiveAnalyticsSnapshot) -> None:
        self._freshness.validate(snapshot)
        if snapshot.greeks is not None:
            self._greeks_cache.put(key, snapshot.greeks)
        self._risk_cache.put(key, snapshot)
        if snapshot.portfolio_greeks is not None:
            self._portfolio_cache.put(key.cache_key(), snapshot.portfolio_greeks)
        if snapshot.position_greeks is not None:
            self._portfolio_cache.put_position(key, snapshot.position_greeks)

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
