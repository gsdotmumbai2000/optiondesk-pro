"""Tests for LiveAnalyticsService.refresh_and_get_analytics(): the
synchronous, on-demand counterpart to request_refresh() (which only submits
to the background dispatcher and returns nothing). Trading workspace's
"Evaluate" action needs the fresh result immediately, not racing a queued
job, so this runs the pipeline inline and returns what it produced.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.greeks.models.greeks_result import GreeksResult
from app.live.cache.greeks_cache import LiveGreeksCache
from app.live.cache.option_cache import LiveOptionCache
from app.live.cache.portfolio_cache import LivePortfolioCache
from app.live.cache.risk_cache import LiveRiskCache
from app.live.dispatcher.calculation_dispatcher import CalculationDispatcher
from app.live.exceptions import LiveCalculationException
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.chain_key import ChainKey
from app.live.option_chain.chain_manager import OptionChainManager
from app.live.refresh.refresh_coordinator import RefreshCoordinator
from app.live.services.live_analytics_service import LiveAnalyticsService
from app.live.services.live_option_chain_service import LiveOptionChainService
from app.live.synchronization.sync_service import SynchronizationService
from app.live.analytics.publisher import AnalyticsPublisher


class _FakePipeline:
    """Duck-typed LiveCalculationPipeline stand-in: only .run(key) is
    exercised by refresh_and_get_analytics()."""

    def __init__(self, result=None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[ChainKey] = []

    def run(self, key: ChainKey):
        self.calls.append(key)
        if self._error is not None:
            raise self._error
        return self._result


def _key() -> ChainKey:
    return ChainKey(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")


def _snapshot(**overrides) -> LiveAnalyticsSnapshot:
    key = _key()
    defaults = dict(
        underlying=key.underlying,
        exchange=key.exchange,
        expiry_date=key.expiry_date,
        greeks=GreeksResult(
            delta=Decimal("0.5"), gamma=Decimal("0.01"), theta=Decimal("-1"),
            vega=Decimal("2"), rho=Decimal("0.3"), vanna=Decimal("0"),
            charm=Decimal("0"), vomma=Decimal("0"),
            calculation_timestamp=datetime.now(timezone.utc),
        ),
        portfolio_greeks={"delta": Decimal("0.5")},
        position_greeks={"delta": Decimal("0.5")},
        calculation_timestamp=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return LiveAnalyticsSnapshot(**defaults)


def _service(pipeline: _FakePipeline) -> LiveAnalyticsService:
    option_cache = LiveOptionCache()
    chain_manager = OptionChainManager(option_cache)
    return LiveAnalyticsService(
        chain_service=LiveOptionChainService(chain_manager, option_cache),
        chain_manager=chain_manager,
        pipeline=pipeline,
        dispatcher=CalculationDispatcher(max_workers=1),
        refresh=RefreshCoordinator(),
        sync=SynchronizationService(),
        publisher=AnalyticsPublisher(event_bus=None),
        greeks_cache=LiveGreeksCache(),
        risk_cache=LiveRiskCache(),
        portfolio_cache=LivePortfolioCache(),
    )


class TestRefreshAndGetAnalyticsSuccess:
    def test_returns_the_snapshot_the_pipeline_produced(self) -> None:
        snapshot = _snapshot()
        pipeline = _FakePipeline(result=snapshot)
        service = _service(pipeline)

        result = service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert result is snapshot
        assert pipeline.calls == [_key()]

    def test_populates_risk_cache_so_get_analytics_reflects_it(self) -> None:
        snapshot = _snapshot()
        service = _service(_FakePipeline(result=snapshot))

        service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert service.get_analytics("NIFTY", "NFO", "18-Aug-2026") is snapshot

    def test_populates_greeks_cache_when_snapshot_has_greeks(self) -> None:
        snapshot = _snapshot()
        service = _service(_FakePipeline(result=snapshot))

        service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert service._greeks_cache.get(_key()) is snapshot.greeks  # noqa: SLF001


class TestRefreshAndGetAnalyticsFailure:
    def test_chain_unavailable_returns_none(self) -> None:
        pipeline = _FakePipeline(error=LiveCalculationException("Live chain unavailable"))
        service = _service(pipeline)

        result = service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert result is None

    def test_failure_does_not_populate_risk_cache(self) -> None:
        pipeline = _FakePipeline(error=LiveCalculationException("Live chain unavailable"))
        service = _service(pipeline)

        service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert service.get_analytics("NIFTY", "NFO", "18-Aug-2026") is None

    def test_stale_timestamp_fails_freshness_validation_and_returns_none(self) -> None:
        from datetime import timedelta

        stale = _snapshot(calculation_timestamp=datetime.now(timezone.utc) - timedelta(minutes=5))
        service = _service(_FakePipeline(result=stale))

        result = service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert result is None


class TestLastRefreshError:
    """last_refresh_error() lets callers (e.g. TradingWorkspaceService's
    Evaluate action) surface the real failure reason instead of a generic
    "unavailable" message."""

    def test_empty_before_any_call(self) -> None:
        service = _service(_FakePipeline(result=_snapshot()))

        assert service.last_refresh_error() == ""

    def test_records_the_exception_message_on_failure(self) -> None:
        pipeline = _FakePipeline(error=LiveCalculationException("Spot quote unavailable: NIFTY"))
        service = _service(pipeline)

        service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert service.last_refresh_error() == "Spot quote unavailable: NIFTY"

    def test_cleared_after_a_subsequent_success(self) -> None:
        pipeline = _FakePipeline(error=LiveCalculationException("Spot quote unavailable: NIFTY"))
        service = _service(pipeline)
        service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")
        assert service.last_refresh_error() != ""

        pipeline._error = None  # noqa: SLF001 -- test control of the fake
        pipeline._result = _snapshot()  # noqa: SLF001
        service.refresh_and_get_analytics("NIFTY", "NFO", "18-Aug-2026")

        assert service.last_refresh_error() == ""
