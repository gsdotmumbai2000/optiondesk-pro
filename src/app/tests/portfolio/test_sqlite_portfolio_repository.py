"""Tests for SqlitePortfolioRepository: real SQLite round-trips, including
a simulated app-restart (new repository instance against the same file).
"""

import sqlite3
from decimal import Decimal
from pathlib import Path

from app.portfolio.models.cash import CashAccount
from app.portfolio.models.portfolio import Portfolio
from app.portfolio.repositories.sqlite_repository import SqlitePortfolioRepository


def _portfolio(portfolio_id: str = "P1", name: str = "Main") -> Portfolio:
    return Portfolio(
        portfolio_id=portfolio_id, name=name,
        cash_account=CashAccount(balance=Decimal("100000"), available=Decimal("80000"), reserved=Decimal("20000")),
        holdings=(), open_positions=(), closed_positions=(),
        pending_orders=(), executed_orders=(), transactions=(),
    )


def _repo(tmp_path: Path) -> SqlitePortfolioRepository:
    repo = SqlitePortfolioRepository(tmp_path / "portfolio.db")
    repo.initialize()
    return repo


class TestSaveAndGet:
    def test_saved_portfolio_is_retrievable_by_id(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        portfolio = _portfolio()

        repo.save(portfolio)

        assert repo.get(portfolio.portfolio_id) == portfolio

    def test_unknown_id_returns_none(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)

        assert repo.get("does-not-exist") is None

    def test_saving_same_id_twice_overwrites(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        repo.save(_portfolio(name="Original"))

        repo.save(_portfolio(name="Renamed"))

        assert repo.get("P1").name == "Renamed"


class TestListCountAndDelete:
    def test_list_ids_and_count_reflect_saved_portfolios(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        repo.save(_portfolio("P1"))
        repo.save(_portfolio("P2"))

        assert set(repo.list_ids()) == {"P1", "P2"}
        assert repo.count() == 2

    def test_delete_removes_portfolio(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        repo.save(_portfolio("P1"))

        repo.delete("P1")

        assert repo.get("P1") is None
        assert repo.count() == 0

    def test_delete_unknown_id_does_not_raise(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)

        repo.delete("does-not-exist")  # must not raise


class TestSurvivesRestart:
    def test_data_is_readable_from_a_new_repository_instance_same_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "portfolio.db"
        first_instance = SqlitePortfolioRepository(db_path)
        first_instance.initialize()
        portfolio = _portfolio()
        first_instance.save(portfolio)
        del first_instance

        second_instance = SqlitePortfolioRepository(db_path)
        second_instance.initialize()

        assert second_instance.get(portfolio.portfolio_id) == portfolio

    def test_data_actually_exists_on_disk_as_a_real_sqlite_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "portfolio.db"
        repo = SqlitePortfolioRepository(db_path)
        repo.initialize()
        repo.save(_portfolio())

        assert db_path.exists()
        with sqlite3.connect(db_path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM portfolios").fetchone()[0]
        assert count == 1
