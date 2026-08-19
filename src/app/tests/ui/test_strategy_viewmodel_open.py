"""Tests for StrategyViewModel.open_strategy(): the "Open" action that must
mark a strategy active in the Trading workspace (the only thing Evaluate/
Optimize/Paper Trade/Refresh Margin check) and signal the UI to switch to
the Trading tab.
"""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.models.ui_enums import UIWorkspaceId
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.strategy_viewmodel import StrategyViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeStrategyService:
    def __init__(self, result: WorkspaceOperationResult) -> None:
        self.result = result
        self.load_calls: list[tuple[str, str]] = []

    def load_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        self.load_calls.append((session_id, strategy_id))
        return self.result


class _FakeTradingService:
    def __init__(self, result: WorkspaceOperationResult) -> None:
        self.result = result
        self.load_calls: list[tuple[str, str]] = []

    def load_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        self.load_calls.append((session_id, strategy_id))
        return self.result


class _FakeCoordinator:
    def __init__(self) -> None:
        self.notified: list[str] = []

    def notify_strategy_loaded(self, strategy_id: str) -> None:
        self.notified.append(strategy_id)


def _make_viewmodel(
    strategy_result: WorkspaceOperationResult,
    trading_result: WorkspaceOperationResult | None = None,
) -> tuple[StrategyViewModel, _FakeStrategyService, _FakeTradingService, _FakeCoordinator]:
    strategy = _FakeStrategyService(strategy_result)
    trading = _FakeTradingService(trading_result or strategy_result)
    coordinator = _FakeCoordinator()
    provider = SimpleNamespace(strategy=strategy, trading=trading, coordinator=coordinator)
    events = SimpleNamespace(strategy_updated=SimpleNamespace(connect=lambda *a, **k: None))
    ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=events, session_id="s1")
    vm = StrategyViewModel(ctx)
    return vm, strategy, trading, coordinator


class TestOpenStrategySuccess:
    def test_marks_strategy_active_in_trading_workspace(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded")
        vm, strategy, trading, _coordinator = _make_viewmodel(result)

        vm.open_strategy("strat-1")

        assert strategy.load_calls == [("s1", "strat-1")]
        assert trading.load_calls == [("s1", "strat-1")]

    def test_notifies_coordinator(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded")
        vm, _strategy, _trading, coordinator = _make_viewmodel(result)

        vm.open_strategy("strat-1")

        assert coordinator.notified == ["strat-1"]

    def test_emits_workspace_switch_to_trading(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded")
        vm, *_ = _make_viewmodel(result)
        received: list[str] = []
        vm.workspace_switch_requested.connect(received.append)

        vm.open_strategy("strat-1")

        assert received == [UIWorkspaceId.TRADING.value]

    def test_status_message_reflects_trading_result(self, qapp: QApplication) -> None:
        strategy_result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy loaded")
        trading_result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded")
        vm, *_ = _make_viewmodel(strategy_result, trading_result)

        vm.open_strategy("strat-1")

        assert vm.status_message == "Strategy loaded"


class TestOpenStrategyFailure:
    def test_strategy_not_found_stops_before_touching_trading(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.STRATEGY, "Strategy not found: strat-1")
        vm, _strategy, trading, coordinator = _make_viewmodel(result)
        received: list[str] = []
        vm.workspace_switch_requested.connect(received.append)

        vm.open_strategy("strat-1")

        assert vm.status_message == "Strategy not found: strat-1"
        assert trading.load_calls == []
        assert coordinator.notified == []
        assert received == []

    def test_trading_load_failure_keeps_strategy_message_and_no_switch(self, qapp: QApplication) -> None:
        strategy_result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy loaded")
        trading_result = WorkspaceOperationResult(False, WorkspaceType.TRADING, "Strategy not found: strat-1")
        vm, *_ = _make_viewmodel(strategy_result, trading_result)
        received: list[str] = []
        vm.workspace_switch_requested.connect(received.append)

        vm.open_strategy("strat-1")

        assert vm.status_message == "Strategy not found: strat-1"
        assert received == []
