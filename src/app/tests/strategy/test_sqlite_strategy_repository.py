"""Tests for SqliteStrategyRepository: real SQLite round-trips, including
a simulated app-restart (new repository instance against the same file).
"""

from decimal import Decimal
from pathlib import Path

from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy
from app.strategy.repository.sqlite_strategy_repository import SqliteStrategyRepository


def _strategy(name: str = "Test Strategy") -> Strategy:
    leg = StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_BUY, quantity=75, premium=Decimal("100"),
        strike=Decimal("24500"), underlying="NIFTY", exchange="NFO",
    )
    return Strategy(metadata=StrategyBuilder(name=name).build().metadata, legs=(leg,))


def _repo(tmp_path: Path) -> SqliteStrategyRepository:
    repo = SqliteStrategyRepository(tmp_path / "strategy.db")
    repo.initialize()
    return repo


class TestSaveAndGet:
    def test_saved_strategy_is_retrievable_by_id(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        strategy = _strategy()

        repo.save(strategy)
        retrieved = repo.get(strategy.strategy_id)

        assert retrieved == strategy

    def test_unknown_id_returns_none(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)

        assert repo.get("does-not-exist") is None

    def test_saving_same_id_twice_overwrites(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        strategy = _strategy(name="Original")
        repo.save(strategy)

        updated = Strategy(metadata=strategy.metadata, legs=())
        repo.save(updated)

        assert repo.get(strategy.strategy_id).legs == ()


class TestListAndDelete:
    def test_list_all_returns_every_saved_strategy(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        s1, s2 = _strategy("One"), _strategy("Two")
        repo.save(s1)
        repo.save(s2)

        all_strategies = repo.list_all()

        assert {s.strategy_id for s in all_strategies} == {s1.strategy_id, s2.strategy_id}

    def test_delete_removes_strategy_and_returns_true(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        strategy = _strategy()
        repo.save(strategy)

        deleted = repo.delete(strategy.strategy_id)

        assert deleted is True
        assert repo.get(strategy.strategy_id) is None

    def test_delete_unknown_id_returns_false(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)

        assert repo.delete("does-not-exist") is False


class TestSurvivesRestart:
    def test_data_is_readable_from_a_new_repository_instance_same_file(self, tmp_path: Path) -> None:
        """Simulates an app restart: a brand new SqliteStrategyRepository
        object, pointed at the same database file, must see data saved by
        a previous instance -- proving persistence, not process-memory."""
        db_path = tmp_path / "strategy.db"
        first_instance = SqliteStrategyRepository(db_path)
        first_instance.initialize()
        strategy = _strategy()
        first_instance.save(strategy)
        del first_instance

        second_instance = SqliteStrategyRepository(db_path)
        second_instance.initialize()
        retrieved = second_instance.get(strategy.strategy_id)

        assert retrieved == strategy

    def test_data_actually_exists_on_disk_as_a_real_sqlite_file(self, tmp_path: Path) -> None:
        import sqlite3

        db_path = tmp_path / "strategy.db"
        repo = SqliteStrategyRepository(db_path)
        repo.initialize()
        repo.save(_strategy())

        assert db_path.exists()
        with sqlite3.connect(db_path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM strategies").fetchone()[0]
        assert count == 1
