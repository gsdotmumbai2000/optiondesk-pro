"""Tests for LiveAnalyticsService.build_evaluation_context(): the raw
context bundle other callers (Trading workspace's "Optimize" action) need
to construct their own StrategyEvaluationRequest/OptimizationRequest,
without going through the tick-driven pipeline.
"""

from types import SimpleNamespace

from app.live.cache.greeks_cache import LiveGreeksCache
from app.live.cache.option_cache import LiveOptionCache
from app.live.cache.portfolio_cache import LivePortfolioCache
from app.live.cache.risk_cache import LiveRiskCache
from app.live.calculations.evaluation_context import EvaluationContext
from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher
from app.live.option_chain.chain_manager import OptionChainManager
from app.live.refresh.refresh_coordinator import RefreshCoordinator
from app.live.services.live_analytics_service import LiveAnalyticsService
from app.live.services.live_option_chain_service import LiveOptionChainService
from app.live.synchronization.sync_service import SynchronizationService
from app.live.analytics.publisher import AnalyticsPublisher


class _FakeContextBuilder:
    """Duck-typed LiveContextBuilder stand-in: records the key it was
    called with and returns canned pieces, or raises on build_option_chain
    to simulate an unsubscribed chain."""

    def __init__(self, *, chain_error: Exception | None = None) -> None:
        self.ctx = SimpleNamespace(name="ctx")
        self.contract = SimpleNamespace(name="contract")
        self.chain = SimpleNamespace(name="chain")
        self.market_snapshot = SimpleNamespace(name="market")
        self.chain_market_snapshot = SimpleNamespace(name="chain_market")
        self.volatility_market_snapshot = SimpleNamespace(name="vol_market")
        self.historical_data = SimpleNamespace(name="historical")
        self._chain_error = chain_error
        self.keys_seen: list = []

    def build_context(self, key):
        self.keys_seen.append(key)
        return self.ctx

    def build_contract(self, key, context):
        return self.contract

    def build_option_chain(self, key, context):
        if self._chain_error is not None:
            raise self._chain_error
        return self.chain

    def build_market_snapshot(self, key, context):
        return self.market_snapshot

    def build_chain_market_snapshot(self, key, context):
        return self.chain_market_snapshot

    def build_volatility_snapshot(self, key, context):
        return self.volatility_market_snapshot

    def build_historical_snapshot(self, key):
        return self.historical_data


def _service(context_builder=None) -> LiveAnalyticsService:
    option_cache = LiveOptionCache()
    chain_manager = OptionChainManager(option_cache)
    return LiveAnalyticsService(
        chain_service=LiveOptionChainService(chain_manager, option_cache),
        chain_manager=chain_manager,
        pipeline=SimpleNamespace(run=lambda key: (_ for _ in ()).throw(AssertionError("not exercised"))),
        dispatcher=CalculationDispatcher(max_workers=1),
        refresh=RefreshCoordinator(),
        sync=SynchronizationService(),
        publisher=AnalyticsPublisher(event_bus=None),
        greeks_cache=LiveGreeksCache(),
        risk_cache=LiveRiskCache(),
        portfolio_cache=LivePortfolioCache(),
        context_builder=context_builder,
    )


class TestBuildEvaluationContextSuccess:
    def test_returns_a_populated_evaluation_context(self) -> None:
        builder = _FakeContextBuilder()
        service = _service(builder)

        result = service.build_evaluation_context("NIFTY", "NFO", "18-Aug-2026")

        assert isinstance(result, EvaluationContext)
        assert result.calculation_context is builder.ctx
        assert result.option_contract is builder.contract
        assert result.option_chain is builder.chain
        assert result.market_snapshot is builder.market_snapshot
        assert result.chain_market_snapshot is builder.chain_market_snapshot
        assert result.volatility_market_snapshot is builder.volatility_market_snapshot
        assert result.historical_data is builder.historical_data

    def test_uses_the_requested_chain_key(self) -> None:
        from app.live.models.chain_key import ChainKey

        builder = _FakeContextBuilder()
        service = _service(builder)

        service.build_evaluation_context("BANKNIFTY", "NFO", "24-Sep-2026")

        assert builder.keys_seen == [ChainKey("BANKNIFTY", "NFO", "24-Sep-2026")]


class TestBuildEvaluationContextFailure:
    def test_no_context_builder_configured_returns_none(self) -> None:
        service = _service(context_builder=None)

        assert service.build_evaluation_context("NIFTY", "NFO", "18-Aug-2026") is None

    def test_chain_unavailable_returns_none(self) -> None:
        builder = _FakeContextBuilder(chain_error=ValueError("Live chain unavailable: NFO:NIFTY:18-Aug-2026"))
        service = _service(builder)

        assert service.build_evaluation_context("NIFTY", "NFO", "18-Aug-2026") is None
