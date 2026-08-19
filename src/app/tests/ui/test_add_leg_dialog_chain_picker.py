"""Tests for AddLegDialog's strike-chain picker: strike/premium/OI/Delta
come from Market workspace's already-loaded option chain snapshot. Each
row's Call/Put cell carries a "B"/"S" button pair -- clicking one picks
that strike, side (Call/Put), and Buy/Sell direction all in one action,
replacing the old separate Side (Buy/Sell) dropdown. Delta columns only
appear when the Settings show_greeks_in_leg_picker preference is on.

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

    def list_underlyings(self) -> list[str]:
        return ["NIFTY"]

    def leg_builder_context(self, underlying: str) -> dict:
        return {"expiries": [("Weekly 18-Aug-2026", _EXPIRY)], "lot_size": 75}

    def leg_chain_strikes(self, underlying: str, expiry: date) -> tuple:
        return self._chain_rows

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

    def test_call_and_put_bs_widgets_are_placed_when_ltp_available(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500"),))

        assert dialog._chain_table.cellWidget(0, dialog._call_bs_column()) is not None
        assert dialog._chain_table.cellWidget(0, dialog._put_bs_column()) is not None

    def test_no_bs_widget_when_side_has_no_ltp(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp=None),))

        assert dialog._chain_table.cellWidget(0, dialog._call_bs_column()) is None
        assert dialog._chain_table.cellWidget(0, dialog._put_bs_column()) is not None


class TestStrikeSelectionByButton:
    def test_clicking_call_buy_selects_ce_buy(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5"),))

        dialog._on_side_selected(0, "CE", "Buy")

        assert dialog._selected_right == "CE"
        assert dialog._selected_side == "Buy"
        assert dialog._selected_strike == Decimal("24500")
        assert dialog._selected_premium == Decimal("135.5")

    def test_clicking_put_sell_selects_pe_sell(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", put_ltp="88.25"),))

        dialog._on_side_selected(0, "PE", "Sell")

        assert dialog._selected_right == "PE"
        assert dialog._selected_side == "Sell"
        assert dialog._selected_strike == Decimal("24500")
        assert dialog._selected_premium == Decimal("88.25")

    def test_selecting_a_side_with_no_ltp_shows_an_error(self, qapp: QApplication) -> None:
        row = _strike_row("24500", call_ltp=None)
        dialog, _vm = _make_dialog((row,))

        dialog._on_side_selected(0, "CE", "Buy")

        assert dialog._selected_right is None
        assert not dialog._error.isHidden()

    def test_selection_label_reflects_the_choice(self, qapp: QApplication) -> None:
        dialog, _vm = _make_dialog((_strike_row("24500", call_ltp="135.5"),))

        dialog._on_side_selected(0, "CE", "Buy")

        assert "Buy CE 24500" in dialog._selection_label.text()


class TestAddingTheSelectedLeg:
    def test_ok_with_a_selected_strike_adds_the_leg(self, qapp: QApplication) -> None:
        dialog, vm = _make_dialog((_strike_row("24500", call_ltp="135.5"),))
        dialog._on_side_selected(0, "CE", "Buy")

        dialog._on_add()

        assert len(vm.added_legs) == 1
        leg = vm.added_legs[0]
        assert leg.strike == Decimal("24500")
        assert leg.premium == Decimal("135.5")
        assert leg.multiplier == 75
        assert leg.underlying == "NIFTY"
        assert leg.expiry == _EXPIRY

    def test_selling_a_put_produces_the_correct_leg_kind(self, qapp: QApplication) -> None:
        from app.strategy.models.enums import LegKind

        dialog, vm = _make_dialog((_strike_row("24500", put_ltp="88.25"),))
        dialog._on_side_selected(0, "PE", "Sell")

        dialog._on_add()

        assert vm.added_legs[0].kind == LegKind.PUT_SELL

    def test_ok_without_a_selection_shows_an_error_and_does_not_add(self, qapp: QApplication) -> None:
        dialog, vm = _make_dialog((_strike_row("24500"),))

        dialog._on_add()

        assert vm.added_legs == []
        assert not dialog._error.isHidden()
        assert "Click Buy or Sell" in dialog._error.text()
