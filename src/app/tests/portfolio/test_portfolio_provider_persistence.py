"""Tests for PortfolioProvider's repository selection: SQLite-backed when a
data_directory is given, in-memory otherwise.
"""

from decimal import Decimal
from pathlib import Path

from app.portfolio.bootstrap import PortfolioProvider
from app.portfolio.models.cash import CashAccount
from app.portfolio.models.portfolio import Portfolio
from app.portfolio.repositories.memory_repository import InMemoryPortfolioRepository
from app.portfolio.repositories.sqlite_repository import SqlitePortfolioRepository


def _portfolio() -> Portfolio:
    return Portfolio(
        portfolio_id="P1", name="Main",
        cash_account=CashAccount(balance=Decimal("100000"), available=Decimal("100000"), reserved=Decimal("0")),
        holdings=(), open_positions=(), closed_positions=(),
        pending_orders=(), executed_orders=(), transactions=(),
    )


class TestNoDataDirectoryUsesInMemoryRepository:
    def test_default_construction_uses_in_memory_repository(self) -> None:
        provider = PortfolioProvider()

        assert isinstance(provider.repository, InMemoryPortfolioRepository)


class TestDataDirectoryUsesSqliteRepository:
    def test_data_directory_selects_sqlite_repository(self, tmp_path: Path) -> None:
        provider = PortfolioProvider(data_directory=tmp_path)

        assert isinstance(provider.repository, SqlitePortfolioRepository)

    def test_database_file_is_created_at_expected_path(self, tmp_path: Path) -> None:
        PortfolioProvider(data_directory=tmp_path)

        assert (tmp_path / "portfolio.db").exists()

    def test_portfolio_saved_survives_a_new_provider_instance(self, tmp_path: Path) -> None:
        portfolio = _portfolio()
        first_provider = PortfolioProvider(data_directory=tmp_path)
        first_provider.repository.save(portfolio)
        del first_provider

        second_provider = PortfolioProvider(data_directory=tmp_path)

        assert second_provider.repository.get(portfolio.portfolio_id) == portfolio
