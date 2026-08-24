"""Tests for TradingViewModel.delete_strategy(): backs the Delete button in
the Open dialog shared by the Strategy Builder's Load button and the
ribbon's Open button.
"""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.trading_viewmodel import TradingViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeStrategyService:
    def __init__(self, delete_result: WorkspaceOperationResult) -> None:
        self._delete_result = delete_result
        self.delete_calls: list[tuple[str, str]] = []

    def delete_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        self.delete_calls.append((session_id, strategy_id))
        return self._delete_result


def _make_viewmodel(
    delete_result: WorkspaceOperationResult,
) -> tuple[TradingViewModel, _FakeStrategyService]:
    strategy_service = _FakeStrategyService(delete_result)
    provider = SimpleNamespace(strategy=strategy_service)
    ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=SimpleNamespace(), session_id="s1")
    return TradingViewModel(ctx), strategy_service


class TestDeleteStrategy:
    def test_calls_service_and_returns_true_on_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy deleted")
        vm, service = _make_viewmodel(result)

        assert vm.delete_strategy("strat-1") is True
        assert service.delete_calls == [("s1", "strat-1")]
        assert vm.status_message == "Strategy deleted"

    def test_returns_false_and_surfaces_message_on_failure(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.STRATEGY, "Strategy not found: strat-1")
        vm, _service = _make_viewmodel(result)

        assert vm.delete_strategy("strat-1") is False
        assert vm.status_message == "Strategy not found: strat-1"
