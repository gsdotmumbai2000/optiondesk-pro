"""Backtesting engine bootstrap."""

from pathlib import Path

from app.events.event_bus import EventBus
from app.backtesting.cache.backtest_cache import BacktestCache
from app.backtesting.engine.backtest_engine import BacktestEngine
from app.backtesting.repository.backtest_result_repository import BacktestResultRepository
from app.backtesting.services.analytics_service import AnalyticsService
from app.backtesting.services.backtest_service import BacktestService
from app.backtesting.services.execution_service import ExecutionService
from app.backtesting.services.replay_service import ReplayService
from app.backtesting.services.report_service import ReportService
from app.backtesting.validation.backtest_validator import BacktestValidator


class BacktestProvider:
    """Wire backtesting engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None, data_directory: Path | None = None) -> None:
        """Initialize provider.

        Named/saved backtest results persist to backtest.db when
        `data_directory` is given; otherwise BacktestService falls back to
        BacktestCache's in-memory named-result slot. The per-run TTL cache
        (BacktestCache.put/get_latest/get_history) always stays in-memory --
        it's an ephemeral cache by design, not meant to survive a restart.
        """
        self.engine = BacktestEngine()
        self.validator = BacktestValidator()
        self.cache = BacktestCache()
        self.repository = None
        if data_directory is not None:
            self.repository = BacktestResultRepository(data_directory / "backtest.db")
            self.repository.initialize()
        self.replay_service = ReplayService()
        self.execution_service = ExecutionService()
        self.analytics_service = AnalyticsService()
        self.report_service = ReportService()
        self.service = BacktestService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
            self.report_service,
            self.repository,
        )
