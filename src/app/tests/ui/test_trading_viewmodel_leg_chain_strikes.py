"""Tests for TradingViewModel.leg_chain_strikes()/show_greeks_in_leg_picker():
the real data feed behind the Add Leg dialog's live strike picker.
"""

from datetime import date
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.session import UserPreferences
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.trading_viewmodel import TradingViewModel

_EXPIRY = date(2026, 8, 18)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeTradingService:
    def __init__(self, result: WorkspaceOperationResult) -> None:
        self.result = result
        self.calls: list[tuple[str, str, str, str]] = []

    def leg_chain_strikes(
        self, session_id: str, underlying: str, exchange: str, expiry_date: str,
    ) -> WorkspaceOperationResult:
        self.calls.append((session_id, underlying, exchange, expiry_date))
        return self.result


class _FakeSettingsService:
    def __init__(self, preferences: UserPreferences) -> None:
        self._preferences = preferences

    def get_preferences(self, session_id: str) -> UserPreferences:
        return self._preferences


def _make_viewmodel(
    result: WorkspaceOperationResult, preferences: UserPreferences | None = None,
) -> tuple[TradingViewModel, _FakeTradingService]:
    trading = _FakeTradingService(result)
    settings = _FakeSettingsService(preferences or UserPreferences())
    provider = SimpleNamespace(trading=trading, settings=settings)
    ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=SimpleNamespace(), session_id="s1")
    return TradingViewModel(ctx), trading


class TestLegChainStrikes:
    def test_success_returns_the_strike_rows_and_formats_the_expiry(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "2 strikes", ["row-a", "row-b"])
        vm, trading = _make_viewmodel(result)

        rows = vm.leg_chain_strikes("NIFTY", _EXPIRY)

        assert rows == ("row-a", "row-b")
        assert trading.calls == [("s1", "NIFTY", "NFO", "18-Aug-2026")]

    def test_failure_returns_empty_tuple_and_sets_status_message(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(
            False, WorkspaceType.TRADING,
            "Live chain unavailable — subscribe to this underlying/expiry in Market workspace first",
        )
        vm, _trading = _make_viewmodel(result)

        rows = vm.leg_chain_strikes("NIFTY", _EXPIRY)

        assert rows == ()
        assert "Live chain unavailable" in vm.status_message

    def test_custom_exchange_is_forwarded(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "0 strikes", [])
        vm, trading = _make_viewmodel(result)

        vm.leg_chain_strikes("BANKNIFTY", _EXPIRY, exchange="BFO")

        assert trading.calls == [("s1", "BANKNIFTY", "BFO", "18-Aug-2026")]


class TestShowGreeksInLegPicker:
    def test_returns_the_stored_preference(self, qapp: QApplication) -> None:
        vm, _trading = _make_viewmodel(
            WorkspaceOperationResult(True, WorkspaceType.TRADING, "ok", []),
            preferences=UserPreferences(show_greeks_in_leg_picker=True),
        )

        assert vm.show_greeks_in_leg_picker() is True

    def test_defaults_to_false(self, qapp: QApplication) -> None:
        vm, _trading = _make_viewmodel(WorkspaceOperationResult(True, WorkspaceType.TRADING, "ok", []))

        assert vm.show_greeks_in_leg_picker() is False
