"""Tests for StrategyProvider's repository selection: SQLite-backed when a
data_directory is given (the real application path), in-memory otherwise
(existing test/caller behavior, unaffected).
"""

from decimal import Decimal
from pathlib import Path

from app.strategy.bootstrap import StrategyProvider
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy
from app.strategy.repository.sqlite_strategy_repository import SqliteStrategyRepository
from app.strategy.repository.strategy_repository import StrategyRepository


def _strategy() -> Strategy:
    leg = StrategyLeg(leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("100"))
    return Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=(leg,))


class TestNoDataDirectoryUsesInMemoryRepository:
    def test_default_construction_uses_in_memory_repository(self) -> None:
        provider = StrategyProvider()

        assert isinstance(provider.repository, StrategyRepository)


class TestDataDirectoryUsesSqliteRepository:
    def test_data_directory_selects_sqlite_repository(self, tmp_path: Path) -> None:
        provider = StrategyProvider(data_directory=tmp_path)

        assert isinstance(provider.repository, SqliteStrategyRepository)

    def test_database_file_is_created_at_expected_path(self, tmp_path: Path) -> None:
        StrategyProvider(data_directory=tmp_path)

        assert (tmp_path / "strategy.db").exists()

    def test_strategy_saved_via_service_survives_a_new_provider_instance(self, tmp_path: Path) -> None:
        """Simulates an app restart at the provider level: a strategy saved
        through one StrategyProvider must be visible to a brand new one
        pointed at the same data_directory."""
        strategy = _strategy()
        first_provider = StrategyProvider(data_directory=tmp_path)
        first_provider.service.create(strategy)
        del first_provider

        second_provider = StrategyProvider(data_directory=tmp_path)
        retrieved = second_provider.repository.get(strategy.strategy_id)

        assert retrieved == strategy
