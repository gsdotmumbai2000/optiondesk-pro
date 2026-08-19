"""Tests for TradingViewModel's Strategy Builder support: add_leg/remove_leg/
new_strategy (the pending-legs staging area) and save_new_strategy() (the
real "Save" action wired to TradingWorkspaceService.create_strategy()).
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.strategy.models.enums import LegKind, StrategyType
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
    def __init__(self, create_result: WorkspaceOperationResult | None = None) -> None:
        self.create_result = create_result
        self.create_calls: list[tuple] = []

    def create_strategy(self, session_id: str, strategy):
        self.create_calls.append((session_id, strategy))
        return self.create_result

    def list_underlyings(self) -> WorkspaceOperationResult:
        return WorkspaceOperationResult(True, WorkspaceType.TRADING, "ok", ["NIFTY", "BANKNIFTY"])

    def leg_builder_context(self, underlying: str) -> WorkspaceOperationResult:
        if underlying != "NIFTY":
            return WorkspaceOperationResult(False, WorkspaceType.TRADING, "unknown")
        return WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "ok",
            {"expiries": [("Weekly 2026-08-18", date(2026, 8, 18))], "lot_size": 75},
        )


def _leg(**overrides) -> StrategyLeg:
    defaults = dict(
        leg_id="leg-1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("120.5"),
        strike=Decimal("24500"), underlying="NIFTY", exchange="NFO",
        expiry=date(2026, 8, 18), multiplier=75,
    )
    defaults.update(overrides)
    return StrategyLeg(**defaults)


def _make_viewmodel(trading: _FakeTradingService) -> tuple[TradingViewModel, _FakeWorker]:
    provider = SimpleNamespace(trading=trading)
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=SimpleNamespace(), session_id="s1")
    vm = TradingViewModel(ctx)
    return vm, worker


class TestPendingLegs:
    def test_add_leg_emits_pending_legs_changed(self, qapp: QApplication) -> None:
        vm, _worker = _make_viewmodel(_FakeTradingService())
        received: list[list] = []
        vm.pending_legs_changed.connect(received.append)

        vm.add_leg(_leg())

        assert len(received) == 1
        assert received[0] == [_leg()]

    def test_remove_leg_emits_remaining_legs(self, qapp: QApplication) -> None:
        vm, _worker = _make_viewmodel(_FakeTradingService())
        vm.add_leg(_leg(leg_id="leg-1"))
        vm.add_leg(_leg(leg_id="leg-2"))
        received: list[list] = []
        vm.pending_legs_changed.connect(received.append)

        vm.remove_leg("leg-1")

        assert len(received[-1]) == 1
        assert received[-1][0].leg_id == "leg-2"

    def test_new_strategy_clears_pending_legs(self, qapp: QApplication) -> None:
        vm, _worker = _make_viewmodel(_FakeTradingService())
        vm.add_leg(_leg())
        received: list[list] = []
        vm.pending_legs_changed.connect(received.append)

        vm.new_strategy()

        assert received == [[]]


class TestLookupWrappers:
    def test_list_underlyings_unwraps_success(self, qapp: QApplication) -> None:
        vm, _worker = _make_viewmodel(_FakeTradingService())

        assert vm.list_underlyings() == ["NIFTY", "BANKNIFTY"]

    def test_leg_builder_context_unwraps_success(self, qapp: QApplication) -> None:
        vm, _worker = _make_viewmodel(_FakeTradingService())

        context = vm.leg_builder_context("NIFTY")

        assert context["lot_size"] == 75
        assert context["expiries"] == [("Weekly 2026-08-18", date(2026, 8, 18))]

    def test_leg_builder_context_failure_returns_empty_dict(self, qapp: QApplication) -> None:
        vm, _worker = _make_viewmodel(_FakeTradingService())

        assert vm.leg_builder_context("UNKNOWN") == {}


class TestSaveNewStrategy:
    def test_no_pending_legs_shows_status_and_does_not_dispatch(self, qapp: QApplication) -> None:
        vm, worker = _make_viewmodel(_FakeTradingService())

        vm.save_new_strategy("My Strategy")

        assert worker.calls == []
        assert vm.status_message == "Add at least one leg before saving"

    def test_builds_strategy_with_recognized_type_and_calls_create(self, qapp: QApplication) -> None:
        trading = _FakeTradingService(
            WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy created")
        )
        vm, worker = _make_viewmodel(trading)
        vm.add_leg(_leg())

        vm.save_new_strategy("My Long Call")
        worker.execute()

        assert len(trading.create_calls) == 1
        session_id, strategy = trading.create_calls[0]
        assert session_id == "s1"
        assert strategy.metadata.name == "My Long Call"
        assert strategy.metadata.recognized_type == StrategyType.LONG_CALL
        assert strategy.legs == (_leg(),)

    def test_success_resets_pending_legs_and_sets_status(self, qapp: QApplication) -> None:
        trading = _FakeTradingService(
            WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy created")
        )
        vm, worker = _make_viewmodel(trading)
        vm.add_leg(_leg())
        received: list[list] = []
        vm.pending_legs_changed.connect(received.append)

        vm.save_new_strategy("My Long Call")
        worker.execute()

        assert received[-1] == []
        assert vm.status_message == "Strategy created"

    def test_failure_keeps_pending_legs_and_shows_message(self, qapp: QApplication) -> None:
        trading = _FakeTradingService(
            WorkspaceOperationResult(False, WorkspaceType.TRADING, "Strategy legs are missing underlying/expiry")
        )
        vm, worker = _make_viewmodel(trading)
        vm.add_leg(_leg())
        received: list[list] = []
        vm.pending_legs_changed.connect(received.append)

        vm.save_new_strategy("My Long Call")
        worker.execute()

        assert received == []  # no reset on failure
        assert vm.status_message == "Strategy legs are missing underlying/expiry"

    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingTradingService(_FakeTradingService):
            def create_strategy(self, session_id: str, strategy):
                raise RuntimeError("db locked")

        vm, worker = _make_viewmodel(_RaisingTradingService())
        vm.add_leg(_leg())
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.save_new_strategy("X")
        worker.execute()

        assert vm.busy is False
        assert errors == ["db locked"]
