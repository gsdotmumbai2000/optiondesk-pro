"""Tests for TradingViewModel.paper_trade(): the "Paper Trade" action wired
to TradingWorkspaceService.paper_trade_active_strategy(), run off the Qt UI
thread via BackgroundWorker and published to the view via
paper_trade_changed.
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

    def paper_trade_active_strategy(self, session_id: str, exchange: str = "NFO") -> WorkspaceOperationResult:
        self.calls.append(session_id)
        return self.result


def _snapshot():
    return SimpleNamespace(
        equity=Decimal("999972.2"), cash_balance=Decimal("1019462.45"),
        open_positions=(SimpleNamespace(),), realized_pnl=Decimal("0"),
    )


def _make_viewmodel(trading: _FakeTradingService) -> tuple[TradingViewModel, _FakeWorker]:
    provider = SimpleNamespace(trading=trading)
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
    vm = TradingViewModel(ctx)
    return vm, worker


class TestPaperTradeSuccess:
    def test_dispatches_to_background_worker_not_ui_thread(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Paper traded 1 leg(s) — equity 999972.2", _snapshot())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.paper_trade()

        assert len(worker.calls) == 1
        assert trading.calls == []  # not called yet -- only queued

    def test_busy_true_while_pending_false_after_completion(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Paper traded", _snapshot())
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.paper_trade()
        assert vm.busy is True
        worker.execute()
        assert vm.busy is False

    def test_emits_paper_trade_changed_with_snapshot(self, qapp: QApplication) -> None:
        snapshot = _snapshot()
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Paper traded", snapshot)
        vm, worker = _make_viewmodel(_FakeTradingService(result))
        received: list = []
        vm.paper_trade_changed.connect(received.append)

        vm.paper_trade()
        worker.execute()

        assert received == [snapshot]

    def test_status_message_reflects_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Paper traded 1 leg(s) — equity 999972.2", _snapshot())
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.paper_trade()
        worker.execute()

        assert vm.status_message == "Paper traded 1 leg(s) — equity 999972.2"

    def test_passes_configured_session_id_to_service(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Paper traded", _snapshot())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.paper_trade()
        worker.execute()

        assert trading.calls == ["s1"]


class TestPaperTradeUnavailableFallsBackGracefully:
    def test_no_active_strategy_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.TRADING, "No active strategy to paper trade")
        vm, worker = _make_viewmodel(_FakeTradingService(result))
        received: list = []
        vm.paper_trade_changed.connect(received.append)

        vm.paper_trade()
        worker.execute()

        assert vm.status_message == "No active strategy to paper trade"
        assert received == []


class TestPaperTradeErrorPath:
    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingTradingService:
            def paper_trade_active_strategy(self, session_id: str, exchange: str = "NFO"):
                raise RuntimeError("paper trading engine unavailable")

        provider = SimpleNamespace(trading=_RaisingTradingService())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
        vm = TradingViewModel(ctx)
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.paper_trade()
        worker.execute()

        assert vm.busy is False
        assert errors == ["paper trading engine unavailable"]
