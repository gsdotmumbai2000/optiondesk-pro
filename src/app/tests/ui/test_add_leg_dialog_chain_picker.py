"""Tests for AddLegDialog's strike-chain picker: strike/premium/OI/Delta
come from Market workspace's already-loaded option chain snapshot. Each
row's Call/Put cell carries a "B"/"S" button pair -- clicking one stages
that strike/side/direction as a leg in the pending-legs list below the
chain (rather than replacing a single in-progress selection), so several
legs can be picked in one dialog session; "Add Legs" commits all of them
at once. Delta columns only appear when the Settings
show_greeks_in_leg_picker preference is on.

Row shape matches OptionStrike.model_dump(mode="json") (the exact payload
TradingWorkspaceService.leg_chain_strikes() returns, read straight from
the WorkspaceCache blob MarketWorkspaceService.initial_option_chain()
writes) -- plain dicts, not a typed live-chain model.
"""

from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.dialogs.add_leg_dialog import AddLegDialog

_EXPIRY = date(2026, 8, 18)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _strike_row(
    strike: str,
    call_ltp: str | None = "120",
    put_ltp: str | None = "90",
    call_oi: int = 1000,
    put_oi: int = 900,
    call_delta: str = "0.5",
    put_delta: str = "-0.4",
) -> dict:
    return {
        "strike_price": strike,
        "call_ltp": call_ltp,
        "put_ltp": put_ltp,
        "call_oi": call_oi,
        "put_oi": put_oi,
        "call_delta": call_delta,
        "put_delta": put_delta,
    }


class _FakeTradingViewModel:
    def __init__(self, chain_rows: tuple = (), show_greeks: bool = False) -> None:
        self._chain_rows = chain_rows
        self._show_greeks = show_greeks
        self.status_message = ""
        self.added_legs: list = []
        self.load_expiry_chain_calls: list = []

    def list_underlyings(self) -> list[str]:
        return ["NIFTY"]

    def leg_builder_context(self, underlying: str) -> dict:
        return {"expiries": [("Weekly 18-Aug-2026", _EXPIRY)], "lot_size": 75}

    def leg_chain_strikes(self, underlying: str, expiry: date) -> tuple:
        return self._chain_rows

    def load_expiry_chain(self, underlying: str, expiry: date, exchange: str = "NFO", *, on_done=None) -> None:
        """Fake: resolves synchronously (no real worker/broker in this test)."""
        self.load_expiry_chain_calls.append((underlying, expiry))
        if on_done:
            on_done()

    def show_greeks_in_leg_picker(self) -> bool:
        return self._show_greeks

    def add_leg(self, leg) -> None:
        self.added_legs.append(leg)


def _make_dialog(chain_rows: tuple = (), show_greeks: bool = False) -> tuple[AddLegDialog, _FakeTradingViewModel]:
    vm = _FakeTradingViewModel(chain_rows, show_greeks)
    return AddLegDialog(vm), vm


class TestChainPopulation:
    def test_rows_render_one_per_strike(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500"), _strike_row("24600")))

        assert dialog._chain_table.rowCount() == 2

    def test_default_columns_exclude_delta(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500"),), show_greeks=False)

        headers = [dialog._chain_table.horizontalHeaderItem(i).text() for i in range(dialog._chain_table.columnCount())]
        assert headers == ["Call B/S", "Call LTP", "Call OI", "Strike", "Put OI", "Put LTP", "Put B/S"]

    def test_greeks_enabled_adds_delta_columns(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500"),), show_greeks=True)

        headers = [dialog._chain_table.horizontalHeaderItem(i).text() for i in range(dialog._chain_table.columnCount())]
        assert headers == [
            "Call Delta", "Call B/S", "Call LTP", "Call OI", "Strike",
            "Put OI", "Put LTP", "Put B/S", "Put Delta",
        ]

    def test_no_chain_shows_the_unavailable_message(self, qapp: QApplication) -> None:
        vm = _FakeTradingViewModel(())
        vm.status_message = "Live chain unavailable — subscribe to this underlying/expiry in Market workspace first"
        dialog = AddLegDialog(vm)

        assert not dialog._error.isHidden()
        assert "Live chain unavailable" in dialog._error.text()

    def test_empty_cache_triggers_a_broker_fetch_for_the_selected_expiry(self, qapp: QApplication) -> None:
        """An expiry Market workspace hasn't loaded yet must not just show
        an error -- it must fetch it fresh via the broker, same as picking
        a different expiry in the Market tab does."""
        vm = _FakeTradingViewModel(())

        dialog = AddLegDialog(vm)

        # _refresh_chain() can run more than once during construction (the
        # combo's currentIndexChanged fires on the first addItem(), and
        # _refresh_expiries() also calls it explicitly) -- what matters is
        # that a fetch for the right underlying/expiry happened at all.
        assert ("NIFTY", _EXPIRY) in vm.load_expiry_chain_calls

    def test_chain_populates_once_the_fetch_lands(self, qapp: QApplication) -> None:
        """Once load_expiry_chain()'s on_done fires and leg_chain_strikes()
        now has rows (simulating the broker fetch having populated the
        session cache), the table must repaint with them."""
        vm = _FakeTradingViewModel(())
        dialog = AddLegDialog(vm)
        assert dialog._chain_table.rowCount() == 0

        vm._chain_rows = (_strike_row("24500"),)
        dialog._on_chain_fetch_done("NIFTY", _EXPIRY)

        assert dialog._chain_table.rowCount() == 1

    def test_stale_fetch_response_is_ignored_after_expiry_changed(self, qapp: QApplication) -> None:
        """A slow fetch for an old expiry selection landing after the user
        already picked a different one must not clobber the newer table."""
        vm = _FakeTradingViewModel(())
        dialog = AddLegDialog(vm)
        dialog._expiry.addItem("Monthly 25-Aug-2026", date(2026, 8, 25))
        dialog._expiry.setCurrentIndex(dialog._expiry.count() - 1)
        vm._chain_rows = (_strike_row("24500"),)

        dialog._on_chain_fetch_done("NIFTY", _EXPIRY)  # stale: the old expiry

        assert dialog._chain_table.rowCount() == 0

    def test_call_and_put_bs_widgets_are_placed_when_ltp_available(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500"),))

        assert dialog._chain_table.cellWidget(0, dialog._call_bs_column()) is not None
        assert dialog._chain_table.cellWidget(0, dialog._put_bs_column()) is not None

    def test_no_bs_widget_when_side_has_no_ltp(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp=None),))

        assert dialog._chain_table.cellWidget(0, dialog._call_bs_column()) is None
        assert dialog._chain_table.cellWidget(0, dialog._put_bs_column()) is not None


class TestStrikeSelectionByButton:
    def test_clicking_call_buy_stages_a_ce_buy_leg(self, qapp: QApplication) -> None:
        from app.strategy.models.enums import LegKind

        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5"),))

        dialog._on_side_selected(0, "CE", "Buy")

        assert len(dialog._pending_legs) == 1
        leg = dialog._pending_legs[0]
        assert leg.kind == LegKind.CALL_BUY
        assert leg.strike == Decimal("24500")
        assert leg.premium == Decimal("135.5")

    def test_clicking_put_sell_stages_a_pe_sell_leg(self, qapp: QApplication) -> None:
        from app.strategy.models.enums import LegKind

        dialog, _vm = _make_dialog((_strike_row("24500", put_ltp="88.25"),))

        dialog._on_side_selected(0, "PE", "Sell")

        assert len(dialog._pending_legs) == 1
        leg = dialog._pending_legs[0]
        assert leg.kind == LegKind.PUT_SELL
        assert leg.strike == Decimal("24500")
        assert leg.premium == Decimal("88.25")

    def test_selecting_a_side_with_no_ltp_shows_an_error_and_stages_nothing(self, qapp: QApplication) -> None:
        row = _strike_row("24500", call_ltp=None)
        dialog, _vm = _make_dialog((row,))

        dialog._on_side_selected(0, "CE", "Buy")

        assert dialog._pending_legs == []
        assert not dialog._error.isHidden()

    def test_clicking_two_rows_stages_both_legs(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5", put_ltp="88.25"),))

        dialog._on_side_selected(0, "CE", "Buy")
        dialog._on_side_selected(0, "PE", "Sell")

        assert len(dialog._pending_legs) == 2
        assert dialog._legs_table.rowCount() == 2

    def test_legs_summary_reflects_staged_count(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5"),))

        dialog._on_side_selected(0, "CE", "Buy")

        assert "1 leg staged" in dialog._legs_summary.text()

    def test_staged_leg_uses_the_current_quantity(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5"),))
        dialog._quantity.setValue(3)

        dialog._on_side_selected(0, "CE", "Buy")

        assert dialog._pending_legs[0].quantity == 3


class TestRemovingAStagedLeg:
    def test_removes_the_leg_at_the_given_index(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5", put_ltp="88.25"),))
        dialog._on_side_selected(0, "CE", "Buy")
        dialog._on_side_selected(0, "PE", "Sell")

        dialog._remove_pending_leg(0)

        assert len(dialog._pending_legs) == 1
        assert dialog._legs_table.rowCount() == 1


class TestAddingTheStagedLegs:
    def test_add_legs_commits_every_staged_leg(self, qapp: QApplication) -> None:
        dialog, vm = _make_dialog((_strike_row("24500", call_ltp="135.5", put_ltp="88.25"),))
        dialog._on_side_selected(0, "CE", "Buy")
        dialog._on_side_selected(0, "PE", "Sell")

        dialog._on_add()

        assert len(vm.added_legs) == 2
        assert vm.added_legs[0].strike == Decimal("24500")
        assert vm.added_legs[0].premium == Decimal("135.5")
        assert vm.added_legs[0].multiplier == 75
        assert vm.added_legs[0].underlying == "NIFTY"
        assert vm.added_legs[0].expiry == _EXPIRY

    def test_add_legs_without_any_staged_shows_an_error_and_does_not_add(self, qapp: QApplication) -> None:
        dialog, vm = _make_dialog((_strike_row("24500"),))

        dialog._on_add()

        assert vm.added_legs == []
        assert not dialog._error.isHidden()
        assert "Click Buy or Sell" in dialog._error.text()
