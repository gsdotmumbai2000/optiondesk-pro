"""Backtest application service."""

from app.events.event_bus import EventBus
from app.backtesting.cache.backtest_cache import BacktestCache
from app.backtesting.engine.backtest_engine import BacktestEngine
from app.backtesting.events import (
    BacktestCompletedEvent,
    PerformanceUpdatedEvent,
    ReplayFinishedEvent,
    ReplayStartedEvent,
    TradeExecutedEvent,
)
from app.backtesting.exceptions import BacktestException
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult
from app.backtesting.providers.cache_keys import build_cache_key
from app.backtesting.repository.backtest_result_repository import BacktestResultRepository
from app.backtesting.services.report_service import ReportService
from app.backtesting.validation.backtest_validator import BacktestValidator


class BacktestService:
    """Orchestrate backtesting, caching, and events."""

    def __init__(
        self,
        engine: BacktestEngine,
        validator: BacktestValidator | None = None,
        cache: BacktestCache | None = None,
        event_bus: EventBus | None = None,
        report_service: ReportService | None = None,
        repository: BacktestResultRepository | None = None,
    ) -> None:
        """Initialize backtest service."""
        self._engine = engine
        self._validator = validator or BacktestValidator()
        self._cache = cache or BacktestCache()
        self._event_bus = event_bus
        self._reports = report_service or ReportService()
        self._repository = repository

    @property
    def cache(self) -> BacktestCache:
        """Return backtest cache."""
        return self._cache

    def run(self, request: BacktestRequest) -> BacktestResult:
        """Run backtest and cache results."""
        try:
            self._validator.validate(request)
            if self._event_bus is not None:
                self._event_bus.publish(ReplayStartedEvent(payload={}))
            result = self._engine.run(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_events(key, result)
            return result
        except BacktestException:
            raise

    def build_report(self, result: BacktestResult):
        """Build backtest report from result."""
        return self._reports.build(result)

    def get_latest(self, request: BacktestRequest) -> BacktestResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def save_result(self, name: str, result: BacktestResult) -> None:
        """Save a named backtest result so it survives a restart.

        Persists to the SQLite-backed repository when one was configured
        (the real application always provides one); otherwise falls back to
        BacktestCache's in-memory named-result slot.
        """
        if self._repository is not None:
            self._repository.save(name, result)
        else:
            self._cache.save(name, result)

    def get_saved_result(self, name: str) -> BacktestResult | None:
        """Return a previously saved named result."""
        if self._repository is not None:
            return self._repository.get(name)
        return self._cache.get_saved(name)

    def list_saved_results(self) -> tuple[str, ...]:
        """Return names of all saved results."""
        if self._repository is not None:
            return self._repository.list_names()
        return ()

    def _publish_events(self, key: str, result: BacktestResult) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(ReplayFinishedEvent(payload={"key": key}))
        self._event_bus.publish(
            BacktestCompletedEvent(payload={"trades": result.total_trades})
        )
        self._event_bus.publish(
            PerformanceUpdatedEvent(
                payload={"sharpe": str(result.sharpe_ratio)}
            )
        )
        if result.trade_log.trades:
            self._event_bus.publish(TradeExecutedEvent(payload={"count": len(result.trade_log.trades)}))
