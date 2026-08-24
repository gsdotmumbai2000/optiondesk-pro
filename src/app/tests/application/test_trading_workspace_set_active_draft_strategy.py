"""Tests for TradingWorkspaceService.set_active_draft_strategy(): registers
a strategy (typically the Strategy Builder's in-progress legs) as the
session's active Trading strategy without persisting it to the strategy
repository -- unlike create_strategy(), so Evaluate can be clicked
repeatedly on an unsaved draft without cluttering the saved strategy list.
"""

from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class _RaisingStrategyEngineService:
    """If set_active_draft_strategy ever calls the repository-persisting
    create()/update() path, this fails the test loudly instead of silently
    writing a row."""

    def create(self, strategy):
        raise AssertionError("set_active_draft_strategy must not persist to the repository")

    def update(self, strategy):
        raise AssertionError("set_active_draft_strategy must not persist to the repository")


def _strategy() -> Strategy:
    leg = StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("100"), strike=Decimal("24500"),
    )
    metadata = StrategyBuilder(name="Draft").build().metadata
    return Strategy(metadata=metadata, legs=(leg,))


def _service() -> tuple[TradingWorkspaceService, SessionManager, WorkspaceCache]:
    sessions = SessionManager()
    cache = WorkspaceCache()
    engines = SimpleNamespace(strategy=SimpleNamespace(service=_RaisingStrategyEngineService()))
    service = TradingWorkspaceService(engines=engines, sessions=sessions, cache=cache)
    return service, sessions, cache


class TestSetActiveDraftStrategy:
    def test_registers_the_strategy_in_the_cache(self) -> None:
        service, sessions, cache = _service()
        session = sessions.create()
        strategy = _strategy()

        service.set_active_draft_strategy(session.session_id, strategy)

        assert cache.get_strategy(strategy.strategy_id) == strategy

    def test_marks_the_strategy_active_in_the_trading_workspace(self) -> None:
        service, sessions, _cache = _service()
        session = sessions.create()
        strategy = _strategy()

        service.set_active_draft_strategy(session.session_id, strategy)

        updated = sessions.get(session.session_id)
        trading_state = next(s for s in updated.workspaces if s.workspace == WorkspaceType.TRADING)
        assert trading_state.entity_id == strategy.strategy_id

    def test_does_not_persist_to_the_strategy_repository(self) -> None:
        service, sessions, _cache = _service()
        session = sessions.create()

        # No AssertionError from _RaisingStrategyEngineService means create()/update() was never called.
        result = service.set_active_draft_strategy(session.session_id, _strategy())

        assert result.success is True

    def test_returns_the_registered_strategy_as_data(self) -> None:
        service, sessions, _cache = _service()
        session = sessions.create()
        strategy = _strategy()

        result = service.set_active_draft_strategy(session.session_id, strategy)

        assert result.data == strategy
