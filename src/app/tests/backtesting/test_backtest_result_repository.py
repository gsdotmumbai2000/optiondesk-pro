"""Tests for BacktestResultRepository: real SQLite round-trips for
explicitly-named/saved backtest results, including a simulated app-restart.
"""

import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

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


def _repo(tmp_path: Path) -> BacktestResultRepository:
    repo = BacktestResultRepository(tmp_path / "backtest.db")
    repo.initialize()
    return repo


class TestSaveAndGet:
    def test_saved_result_is_retrievable_by_name(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        result = _result()

        repo.save("iron-condor-run-1", result)

        assert repo.get("iron-condor-run-1") == result

    def test_unknown_name_returns_none(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)

        assert repo.get("does-not-exist") is None

    def test_saving_same_name_twice_overwrites(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        repo.save("run-1", _result())

        second = replace(_result(), total_trades=999)
        repo.save("run-1", second)

        assert repo.get("run-1").total_trades == 999


class TestListAndDelete:
    def test_list_names_returns_all_saved_result_names(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        repo.save("run-a", _result())
        repo.save("run-b", _result())

        assert set(repo.list_names()) == {"run-a", "run-b"}

    def test_delete_removes_result_and_returns_true(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        repo.save("run-1", _result())

        assert repo.delete("run-1") is True
        assert repo.get("run-1") is None

    def test_delete_unknown_name_returns_false(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)

        assert repo.delete("does-not-exist") is False


class TestSurvivesRestart:
    def test_data_is_readable_from_a_new_repository_instance_same_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "backtest.db"
        first_instance = BacktestResultRepository(db_path)
        first_instance.initialize()
        result = _result()
        first_instance.save("saved-run", result)
        del first_instance

        second_instance = BacktestResultRepository(db_path)
        second_instance.initialize()

        assert second_instance.get("saved-run") == result

    def test_data_actually_exists_on_disk_as_a_real_sqlite_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "backtest.db"
        repo = BacktestResultRepository(db_path)
        repo.initialize()
        repo.save("run-1", _result())

        assert db_path.exists()
        with sqlite3.connect(db_path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM backtest_results").fetchone()[0]
        assert count == 1
