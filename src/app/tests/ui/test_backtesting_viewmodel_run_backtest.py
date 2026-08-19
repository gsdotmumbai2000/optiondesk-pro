"""Tests for BacktestingViewModel.run_backtest(): the "Run" action wired to
BacktestingWorkspaceService.run_active_strategy_backtest(), run off the Qt
UI thread via BackgroundWorker since it's a real broker REST call, and
published to the view via result_changed.
"""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.backtesting.models.trades import EquityCurve
from app.ui.viewmodels.backtesting_viewmodel import BacktestingViewModel
from app.ui.viewmodels.context import ViewModelContext


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


class _FakeBacktestingService:
    def __init__(self, result: WorkspaceOperationResult) -> None:
        self.result = result
        self.calls: list[str] = []

    def run_active_strategy_backtest(self, session_id: str) -> WorkspaceOperationResult:
        self.calls.append(session_id)
        return self.result


class _FakeCoordinator:
    def __init__(self) -> None:
        self.notified: list[str] = []

    def notify_backtest_started(self, session_id: str) -> None:
        self.notified.append(session_id)


def _backtest_result():
    return SimpleNamespace(equity_curve=EquityCurve(points=()), total_trades=0)


def _make_viewmodel(backtesting: _FakeBacktestingService) -> tuple[BacktestingViewModel, _FakeWorker]:
    provider = SimpleNamespace(backtesting=backtesting, coordinator=_FakeCoordinator())
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
    vm = BacktestingViewModel(ctx)
    return vm, worker


class TestRunBacktestSuccess:
    def test_dispatches_to_background_worker_not_ui_thread(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", _backtest_result())
        backtesting = _FakeBacktestingService(result)
        vm, worker = _make_viewmodel(backtesting)

        vm.run_backtest()

        assert len(worker.calls) == 1
        assert backtesting.calls == []  # not called yet -- only queued

    def test_busy_true_while_pending_false_after_completion(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", _backtest_result())
        vm, worker = _make_viewmodel(_FakeBacktestingService(result))

        vm.run_backtest()
        assert vm.busy is True
        worker.execute()
        assert vm.busy is False

    def test_emits_result_changed_with_backtest_result(self, qapp: QApplication) -> None:
        backtest_result = _backtest_result()
        result = WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", backtest_result)
        vm, worker = _make_viewmodel(_FakeBacktestingService(result))
        received: list = []
        vm.result_changed.connect(received.append)

        vm.run_backtest()
        worker.execute()

        assert received == [backtest_result]

    def test_run_state_becomes_completed(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", _backtest_result())
        vm, worker = _make_viewmodel(_FakeBacktestingService(result))

        vm.run_backtest()
        worker.execute()

        assert vm.run_state == "COMPLETED"

    def test_status_message_reflects_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", _backtest_result())
        vm, worker = _make_viewmodel(_FakeBacktestingService(result))

        vm.run_backtest()
        worker.execute()

        assert vm.status_message == "Backtest complete"

    def test_notifies_coordinator_backtest_started_synchronously(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", _backtest_result())
        backtesting = _FakeBacktestingService(result)
        provider = SimpleNamespace(backtesting=backtesting, coordinator=_FakeCoordinator())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
        vm = BacktestingViewModel(ctx)

        vm.run_backtest()

        assert provider.coordinator.notified == ["s1"]


class TestRunBacktestUnavailableFallsBackGracefully:
    def test_no_active_strategy_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.BACKTESTING, "No active strategy to backtest")
        vm, worker = _make_viewmodel(_FakeBacktestingService(result))
        received: list = []
        vm.result_changed.connect(received.append)

        vm.run_backtest()
        worker.execute()

        assert vm.status_message == "No active strategy to backtest"
        assert received == []
        assert vm.run_state == "IDLE"  # unchanged from initial default

    def test_no_historical_data_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            False, WorkspaceType.BACKTESTING,
            "Historical data unavailable — connect a broker to backtest against real history",
        )
        vm, worker = _make_viewmodel(_FakeBacktestingService(result))

        vm.run_backtest()
        worker.execute()

        assert "Historical data unavailable" in vm.status_message


class TestRunBacktestErrorPath:
    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingBacktestingService:
            def run_active_strategy_backtest(self, session_id: str):
                raise RuntimeError("broker connection lost")

        provider = SimpleNamespace(backtesting=_RaisingBacktestingService(), coordinator=_FakeCoordinator())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
        vm = BacktestingViewModel(ctx)
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.run_backtest()
        worker.execute()

        assert vm.busy is False
        assert errors == ["broker connection lost"]
