"""Tests for TradingViewModel.refresh_margin(): the "Refresh Margin" action
wired to TradingWorkspaceService.refresh_margin(), run off the Qt UI thread
via BackgroundWorker since it's a real broker REST call.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.margin.models.broker_response import BrokerMarginResponse
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
    threads -- exercised synchronously via execute(), matching the pattern
    used by MarketViewModel's async tests."""

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

    def refresh_margin(self, session_id: str, exchange: str = "NFO") -> WorkspaceOperationResult:
        self.calls.append(session_id)
        return self.result


def _broker_response() -> BrokerMarginResponse:
    from datetime import datetime, timezone

    return BrokerMarginResponse(
        broker_id="BREEZE", initial_margin=Decimal("9000"), exposure_margin=Decimal("2000"),
        span_margin=Decimal("7000"), total_margin=Decimal("9000"),
        available_margin=Decimal("41000"), account_balance=Decimal("100000"),
        captured_at=datetime.now(timezone.utc),
    )


def _make_viewmodel(trading: _FakeTradingService) -> tuple[TradingViewModel, _FakeWorker]:
    provider = SimpleNamespace(trading=trading)
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
    vm = TradingViewModel(ctx)
    return vm, worker


class TestRefreshMarginSuccess:
    def test_dispatches_to_background_worker_not_ui_thread(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Broker margin refreshed", _broker_response(),
        )
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.refresh_margin()

        assert len(worker.calls) == 1
        assert trading.calls == []  # not called yet -- only queued, not executed

    def test_busy_true_while_pending_false_after_completion(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Broker margin refreshed", _broker_response(),
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.refresh_margin()
        assert vm.busy is True
        worker.execute()
        assert vm.busy is False

    def test_updates_margin_summary_with_broker_figures(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Broker margin refreshed", _broker_response(),
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.refresh_margin()
        worker.execute()

        assert "BREEZE" in vm.margin_summary
        assert "7000" in vm.margin_summary
        assert "2000" in vm.margin_summary
        assert "9000" in vm.margin_summary

    def test_status_message_reflects_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Broker margin refreshed", _broker_response(),
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.refresh_margin()
        worker.execute()

        assert vm.status_message == "Broker margin refreshed"

    def test_passes_configured_session_id_to_service(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Broker margin refreshed", _broker_response(),
        )
        trading = _FakeTradingService(result)
        vm, worker = _make_viewmodel(trading)

        vm.refresh_margin()
        worker.execute()

        assert trading.calls == ["s1"]


class TestRefreshMarginUnavailableFallsBackGracefully:
    def test_no_active_strategy_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            False, WorkspaceType.TRADING, "No active strategy to refresh margin for",
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.refresh_margin()
        worker.execute()

        assert vm.status_message == "No active strategy to refresh margin for"
        assert vm.margin_summary == "Margin: —"  # unchanged from initial default

    def test_broker_unavailable_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            False, WorkspaceType.TRADING, "Broker margin unavailable — showing estimate",
        )
        vm, worker = _make_viewmodel(_FakeTradingService(result))

        vm.refresh_margin()
        worker.execute()

        assert vm.status_message == "Broker margin unavailable — showing estimate"


class TestRefreshMarginErrorPath:
    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingTradingService:
            def refresh_margin(self, session_id: str, exchange: str = "NFO"):
                raise RuntimeError("broker connection lost")

        provider = SimpleNamespace(trading=_RaisingTradingService())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
        vm = TradingViewModel(ctx)
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.refresh_margin()
        worker.execute()

        assert vm.busy is False
        assert errors == ["broker connection lost"]
