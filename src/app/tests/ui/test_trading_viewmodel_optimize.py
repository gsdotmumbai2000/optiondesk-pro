"""Tests for TradingViewModel.optimize(): the "Optimize" action wired to
TradingWorkspaceService.optimize_active_strategy(), run off the Qt UI
thread via BackgroundWorker and published to the view via
optimization_changed.
"""

from decimal import Decimal
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


class _FakeWorker:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def run(self, fn, on_finished, on_error) -> None:
        self.calls.append((fn, on_finished, on_error))

    def execute(self, index: int = -1) -> None:
        fn, done, err = self.calls[index]
        try:
            result = fn()
        except Exception as exc:  # noqa: BLE001
            err(str(exc))
            return
        done(result)


class _FakeTradingService:
    def __init__(self, result: WorkspaceOperationResult) -> None:
        self.result = result
        self.calls: list[str] = []

    def optimize_active_strategy(self, session_id: str, exchange: str = "NFO") -> WorkspaceOperationResult:
        self.calls.append(session_id)
        return self.result


def _optimization_result():
    return SimpleNamespace(
        candidate_strategies=(1, 2, 3), overall_score=Decimal("82"), recommendation="Consider this variant",
    )


def _make_viewmodel(trading: _FakeTradingService) -> tuple[TradingViewModel, _FakeWorker]:
    provider = SimpleNamespace(trading=trading)
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
    vm = TradingViewModel(ctx)
    return vm, worker


class TestOptimizeSuccess:
    def test_dispatches_to_background_worker_not_ui_thread(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Optimization complete", _optimization_result())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.optimize()

        assert len(worker.calls) == 1
        assert trading.calls == []  # not called yet -- only queued

    def test_busy_true_while_pending_false_after_completion(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Optimization complete", _optimization_result())
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.optimize()
        assert vm.busy is True
        worker.execute()
        assert vm.busy is False

    def test_emits_optimization_changed_with_result(self, qapp: QApplication) -> None:
        optimization_result = _optimization_result()
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Optimization complete", optimization_result)
        vm, worker = _make_viewmodel(_FakeTradingService(result))
        received: list = []
        vm.optimization_changed.connect(received.append)

        vm.optimize()
        worker.execute()

        assert received == [optimization_result]

    def test_status_message_reflects_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Optimization complete", _optimization_result())
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.optimize()
        worker.execute()

        assert vm.status_message == "Optimization complete"

    def test_passes_configured_session_id_to_service(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Optimization complete", _optimization_result())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.optimize()
        worker.execute()

        assert trading.calls == ["s1"]


class TestOptimizeUnavailableFallsBackGracefully:
    def test_no_active_strategy_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.TRADING, "No active strategy to optimize")
        vm, worker = _make_viewmodel(_FakeTradingService(result))
        received: list = []
        vm.optimization_changed.connect(received.append)

        vm.optimize()
        worker.execute()

        assert vm.status_message == "No active strategy to optimize"
        assert received == []

    def test_live_analytics_unavailable_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            False, WorkspaceType.TRADING, "Live analytics unavailable for this strategy — evaluate it first",
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.optimize()
        worker.execute()

        assert "Live analytics unavailable" in vm.status_message


class TestOptimizeErrorPath:
    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingTradingService:
            def optimize_active_strategy(self, session_id: str, exchange: str = "NFO"):
                raise RuntimeError("optimizer engine unavailable")

        provider = SimpleNamespace(trading=_RaisingTradingService())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
        vm = TradingViewModel(ctx)
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.optimize()
        worker.execute()

        assert vm.busy is False
        assert errors == ["optimizer engine unavailable"]
