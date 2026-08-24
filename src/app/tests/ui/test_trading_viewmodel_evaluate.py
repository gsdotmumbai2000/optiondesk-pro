"""Tests for TradingViewModel.evaluate(): the "Evaluate" action wired to
TradingWorkspaceService.evaluate_active_strategy(), run off the Qt UI thread
via BackgroundWorker and published to the view via evaluation_changed.

Evaluate first registers the builder's current legs as this session's
active strategy (set_active_draft_strategy -- cache-only, not persisted)
so it works on whatever's in the leg table without requiring an explicit
Save first; only then does it dispatch evaluate_active_strategy() to the
background worker.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.trading_viewmodel import TradingViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeWorker:
    """BackgroundWorker double that records dispatches instead of running
    threads -- exercised synchronously via execute()."""

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
        self.registered_drafts: list = []

    def set_active_draft_strategy(self, session_id: str, strategy) -> WorkspaceOperationResult:
        self.registered_drafts.append((session_id, strategy))
        return WorkspaceOperationResult(True, WorkspaceType.TRADING, "Draft strategy active", strategy)

    def evaluate_active_strategy(self, session_id: str, exchange: str = "NFO") -> WorkspaceOperationResult:
        self.calls.append(session_id)
        return self.result


def _leg() -> StrategyLeg:
    return StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("100"),
        strike=Decimal("24500"), expiry=date(2026, 8, 18), underlying="NIFTY", exchange="NFO",
    )


def _snapshot() -> LiveAnalyticsSnapshot:
    return LiveAnalyticsSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        calculation_timestamp=datetime.now(timezone.utc),
    )


def _make_viewmodel(trading: _FakeTradingService, with_leg: bool = True) -> tuple[TradingViewModel, _FakeWorker]:
    provider = SimpleNamespace(trading=trading)
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
    vm = TradingViewModel(ctx)
    if with_leg:
        vm.add_leg(_leg())
    return vm, worker


class TestEvaluateRegistersTheBuilderAsTheActiveStrategyFirst:
    def test_registers_the_builders_current_legs_before_dispatching(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", _snapshot())
        trading = _FakeTradingService(result)
        vm, _worker = _make_viewmodel(trading)

        vm.evaluate()

        assert len(trading.registered_drafts) == 1
        session_id, strategy = trading.registered_drafts[0]
        assert session_id == "s1"
        assert strategy.legs == (_leg(),)

    def test_no_legs_shows_a_status_message_and_never_dispatches(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", _snapshot())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading, with_leg=False)

        vm.evaluate()

        assert vm.status_message == "Add at least one leg before evaluating"
        assert worker.calls == []
        assert trading.registered_drafts == []


class TestEvaluateSuccess:
    def test_dispatches_to_background_worker_not_ui_thread(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", _snapshot())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.evaluate()

        assert len(worker.calls) == 1
        assert trading.calls == []  # not called yet -- only queued, not executed

    def test_busy_true_while_pending_false_after_completion(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", _snapshot())
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.evaluate()
        assert vm.busy is True
        worker.execute()
        assert vm.busy is False

    def test_emits_evaluation_changed_with_snapshot(self, qapp: QApplication) -> None:
        snapshot = _snapshot()
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", snapshot)
        vm, worker = _make_viewmodel(_FakeTradingService(result))
        received: list = []
        vm.evaluation_changed.connect(received.append)

        vm.evaluate()
        worker.execute()

        assert received == [snapshot]

    def test_status_message_reflects_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", _snapshot())
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.evaluate()
        worker.execute()

        assert vm.status_message == "Strategy evaluated"

    def test_passes_configured_session_id_to_service(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", _snapshot())
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.evaluate()
        worker.execute()

        assert trading.calls == ["s1"]


class TestEvaluateUnavailableFallsBackGracefully:
    def test_no_active_strategy_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.TRADING, "No active strategy to evaluate")
        vm, worker = _make_viewmodel(_FakeTradingService(result))
        received: list = []
        vm.evaluation_changed.connect(received.append)

        vm.evaluate()
        worker.execute()

        assert vm.status_message == "No active strategy to evaluate"
        assert received == []  # no snapshot emitted on failure

    def test_chain_unavailable_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            False, WorkspaceType.TRADING,
            "Live chain unavailable — subscribe to this underlying/expiry in Market workspace first",
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.evaluate()
        worker.execute()

        assert "Live chain unavailable" in vm.status_message


class TestEvaluateErrorPath:
    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingTradingService:
            def set_active_draft_strategy(self, session_id: str, strategy):
                return WorkspaceOperationResult(True, WorkspaceType.TRADING, "Draft strategy active", strategy)

            def evaluate_active_strategy(self, session_id: str, exchange: str = "NFO"):
                raise RuntimeError("chain manager unavailable")

        provider = SimpleNamespace(trading=_RaisingTradingService())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
        vm = TradingViewModel(ctx)
        vm.add_leg(_leg())
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.evaluate()
        worker.execute()

        assert vm.busy is False
        assert errors == ["chain manager unavailable"]
