"""Tests for StrategyViewModel.delete_strategy(): removes a saved strategy
and refreshes the list on success, leaving the list untouched on failure.
"""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.strategy_viewmodel import StrategyViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeStrategyService:
    def __init__(self, delete_result: WorkspaceOperationResult) -> None:
        self.delete_result = delete_result
        self.delete_calls: list[tuple[str, str]] = []
        self.list_calls: list[str] = []

    def delete_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        self.delete_calls.append((session_id, strategy_id))
        return self.delete_result

    def list_strategies(self, session_id: str) -> WorkspaceOperationResult:
        self.list_calls.append(session_id)
        return WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "0 strategies", [])


def _make_viewmodel(
    delete_result: WorkspaceOperationResult,
) -> tuple[StrategyViewModel, _FakeStrategyService]:
    strategy = _FakeStrategyService(delete_result)
    provider = SimpleNamespace(strategy=strategy)
    events = SimpleNamespace(strategy_updated=SimpleNamespace(connect=lambda *a, **k: None))
    ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=events, session_id="s1")
    vm = StrategyViewModel(ctx)
    return vm, strategy


class TestDeleteStrategySuccess:
    def test_calls_service_with_session_and_id(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy deleted")
        vm, strategy = _make_viewmodel(result)

        vm.delete_strategy("strat-1")

        assert strategy.delete_calls == [("s1", "strat-1")]

    def test_refreshes_list_after_delete(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy deleted")
        vm, strategy = _make_viewmodel(result)

        vm.delete_strategy("strat-1")

        assert strategy.list_calls == ["s1"]

    def test_status_message_reflects_result(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy deleted")
        vm, _strategy = _make_viewmodel(result)

        vm.delete_strategy("strat-1")

        assert vm.status_message == "Strategy deleted"


class TestDeleteStrategyFailure:
    def test_not_found_does_not_refresh(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.STRATEGY, "Strategy not found: strat-1")
        vm, strategy = _make_viewmodel(result)

        vm.delete_strategy("strat-1")

        assert vm.status_message == "Strategy not found: strat-1"
        assert strategy.list_calls == []
