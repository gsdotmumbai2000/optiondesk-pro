"""Tests for BacktestProvider/BacktestService's save_result()/
get_saved_result()/list_saved_results(): SQLite-backed when a
data_directory is given, falling back to BacktestCache's in-memory named-
result slot otherwise. Distinct from the per-run TTL cache, which always
stays in-memory regardless.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from app.backtesting.bootstrap import BacktestProvider
from app.backtesting.models.metrics import PerformanceMetrics
from app.backtesting.models.result import BacktestResult
from app.backtesting.models.trades import DrawdownCurve, EquityCurve, TradeLog
from app.backtesting.repository.backtest_result_repository import BacktestResultRepository


def _result() -> BacktestResult:
    metrics = PerformanceMetrics(
        sharpe_ratio=Decimal("1.5"), sortino_ratio=Decimal("2"), calmar_ratio=Decimal("3"),
        profit_factor=Decimal("2"), expectancy=Decimal("100"), recovery_factor=Decimal("1"),
        return_on_capital=Decimal("0.1"), win_rate=Decimal("0.6"), loss_rate=Decimal("0.4"),
        average_win=Decimal("200"), average_loss=Decimal("-100"), largest_win=Decimal("1000"),
        largest_loss=Decimal("-500"), max_consecutive_wins=3, max_consecutive_losses=2,
        total_trades=50, winning_trades=30, losing_trades=20,
        average_holding_time=timedelta(hours=4), capital_utilization=Decimal("0.5"),
        margin_utilization=Decimal("0.3"),
    )
    return BacktestResult(
        total_return=Decimal("0.1"), net_profit=Decimal("10000"), gross_profit=Decimal("15000"),
        gross_loss=Decimal("-5000"), maximum_drawdown=Decimal("-2000"), profit_factor=Decimal("2"),
        sharpe_ratio=Decimal("1.5"), sortino_ratio=Decimal("2"), calmar_ratio=Decimal("3"),
        expectancy=Decimal("100"), win_rate=Decimal("0.6"), loss_rate=Decimal("0.4"),
        average_win=Decimal("200"), average_loss=Decimal("-100"), largest_win=Decimal("1000"),
        largest_loss=Decimal("-500"), maximum_consecutive_wins=3, maximum_consecutive_losses=2,
        total_trades=50, winning_trades=30, losing_trades=20,
        average_holding_time=timedelta(hours=4), capital_utilization=Decimal("0.5"),
        margin_utilization=Decimal("0.3"), equity_curve=EquityCurve(points=()),
        drawdown_curve=DrawdownCurve(points=()), trade_log=TradeLog(trades=()),
        performance_metrics=metrics, simulation_timestamp=datetime(2026, 8, 16, tzinfo=timezone.utc),
    )


class TestNoDataDirectoryFallsBackToInMemoryCache:
    def test_repository_is_none(self) -> None:
        provider = BacktestProvider()

        assert provider.repository is None

    def test_save_and_get_result_work_via_in_memory_cache_fallback(self) -> None:
        provider = BacktestProvider()
        result = _result()

        provider.service.save_result("run-1", result)

        assert provider.service.get_saved_result("run-1") == result

    def test_list_saved_results_returns_empty_without_a_repository(self) -> None:
        """The in-memory BacktestCache fallback has no listing capability --
        this is a documented limitation, not a crash."""
        provider = BacktestProvider()
        provider.service.save_result("run-1", _result())

        assert provider.service.list_saved_results() == ()


class TestDataDirectoryUsesSqliteRepository:
    def test_data_directory_selects_sqlite_repository(self, tmp_path: Path) -> None:
        provider = BacktestProvider(data_directory=tmp_path)

        assert isinstance(provider.repository, BacktestResultRepository)

    def test_database_file_is_created_at_expected_path(self, tmp_path: Path) -> None:
        BacktestProvider(data_directory=tmp_path)

        assert (tmp_path / "backtest.db").exists()

    def test_saved_result_survives_a_new_provider_instance(self, tmp_path: Path) -> None:
        result = _result()
        first_provider = BacktestProvider(data_directory=tmp_path)
        first_provider.service.save_result("saved-run", result)
        del first_provider

        second_provider = BacktestProvider(data_directory=tmp_path)

        assert second_provider.service.get_saved_result("saved-run") == result

    def test_list_saved_results_reflects_all_saved_names(self, tmp_path: Path) -> None:
        provider = BacktestProvider(data_directory=tmp_path)
        provider.service.save_result("run-a", _result())
        provider.service.save_result("run-b", _result())

        assert set(provider.service.list_saved_results()) == {"run-a", "run-b"}

    def test_per_run_ttl_cache_stays_in_memory_regardless_of_data_directory(self, tmp_path: Path) -> None:
        """BacktestCache.put()/get_latest() (the ephemeral per-run cache) is
        unaffected by data_directory -- only the named save_result() path
        uses the repository."""
        provider = BacktestProvider(data_directory=tmp_path)
        provider.cache.put("key-1", _result())

        assert provider.cache.get_latest("key-1") is not None
        second = BacktestProvider(data_directory=tmp_path)
        assert second.cache.get_latest("key-1") is None  # new cache instance, never persisted
