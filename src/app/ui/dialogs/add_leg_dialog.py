"""Add-leg dialog for the Strategy Builder: strike/premium/OI/Delta are
pulled from the option chain already loaded in Market workspace, not typed
in. Each row's Call/Put cell carries small "B"/"S" buttons -- clicking one
picks that strike, that side (Call/Put), and Buy/Sell all in one action, so
there's no separate Side field duplicating what the chain already shows.
Delta columns only appear when the user has turned them on in Settings
(show_greeks_in_leg_picker)."""

from datetime import date
from decimal import Decimal
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                                 QHBoxLayout, QHeaderView, QLabel, QSpinBox, QTableWidget,
                                 QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.ui.viewmodels.trading_viewmodel import TradingViewModel
from app.utils.uuid_helper import generate_uuid

_KIND_BY_RIGHT_SIDE = {
    ("CE", "Buy"): LegKind.CALL_BUY,
    ("CE", "Sell"): LegKind.CALL_SELL,
    ("PE", "Buy"): LegKind.PUT_BUY,
    ("PE", "Sell"): LegKind.PUT_SELL,
}


def build_leg_from_strike(
    *,
    underlying: str,
    exchange: str,
    expiry: date,
    right: str,
    side: str,
    lots: int,
    strike: Decimal,
    premium: Decimal,
    lot_size: int,
) -> StrategyLeg:
    """Build a StrategyLeg from a strike picked off the live chain --
    strike/premium are already real chain values, not user-typed text, so
    there's nothing left to parse here beyond the kind mapping and the one
    input that's still free-form: lot count. Raises ValueError with a
    user-facing message on an unsupported kind or non-positive lots."""
    kind = _KIND_BY_RIGHT_SIDE.get((right, side))
    if kind is None:
        raise ValueError(f"Unsupported right/side combination: {right}/{side}")
    if lots <= 0:
        raise ValueError("Quantity must be at least 1 lot")
    return StrategyLeg(
        leg_id=generate_uuid(),
        kind=kind,
        quantity=lots,
        premium=premium,
        strike=strike,
        expiry=expiry,
        multiplier=lot_size,
        underlying=underlying,
        exchange=exchange,
    )


def _fmt(value: object) -> str:
    return "—" if value is None else str(value)


def _to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001 -- malformed chain data must not crash the picker
        return None


class AddLegDialog(QDialog):
    """Collects one option leg -- underlying/expiry/quantity plus a
    strike+right+side picked from the live chain -- and adds it to the
    strategy currently being built, via TradingViewModel.add_leg()."""

    def __init__(self, view_model: TradingViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._lot_size = 1
        self._show_greeks = view_model.show_greeks_in_leg_picker()
        self._chain_rows: list = []
        self._selected_right: str | None = None
        self._selected_side: str | None = None
        self._selected_strike: Decimal | None = None
        self._selected_premium: Decimal | None = None
        self.setWindowTitle("Add Leg")
        self.setMinimumSize(560, 480)

        self._underlying = QComboBox()
        self._underlying.addItems(self._vm.list_underlyings())
        self._expiry = QComboBox()
        self._quantity = QSpinBox()
        self._quantity.setRange(1, 10_000)
        self._quantity.setValue(1)

        form = QFormLayout()
        form.addRow("Underlying", self._underlying)
        form.addRow("Expiry", self._expiry)
        form.addRow("Quantity (lots)", self._quantity)

        self._chain_table = QTableWidget(0, 0)
        self._chain_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._chain_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._chain_table.verticalHeader().setVisible(False)
        self._chain_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self._selection_label = QLabel("No strike selected — click B or S on a Call/Put row below")
        self._error = QLabel()
        self._error.setStyleSheet("color: #d9534f;")
        self._error.setVisible(False)

        self._underlying.currentTextChanged.connect(self._refresh_expiries)
        self._expiry.currentIndexChanged.connect(self._refresh_chain)
        self._refresh_expiries(self._underlying.currentText())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_add)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._chain_table)
        layout.addWidget(self._selection_label)
        layout.addWidget(self._error)
        layout.addWidget(buttons)

    def _chain_columns(self) -> list[str]:
        if self._show_greeks:
            return ["Call Delta", "Call B/S", "Call LTP", "Call OI", "Strike", "Put OI", "Put LTP", "Put B/S", "Put Delta"]
        return ["Call B/S", "Call LTP", "Call OI", "Strike", "Put OI", "Put LTP", "Put B/S"]

    def _strike_column(self) -> int:
        return 4 if self._show_greeks else 3

    def _call_bs_column(self) -> int:
        return 1 if self._show_greeks else 0

    def _put_bs_column(self) -> int:
        return 7 if self._show_greeks else 6

    def _refresh_expiries(self, underlying: str) -> None:
        self._expiry.clear()
        if not underlying:
            self._refresh_chain()
            return
        context = self._vm.leg_builder_context(underlying)
        for label, expiry_date in context.get("expiries", []):
            self._expiry.addItem(label, expiry_date)
        self._lot_size = context.get("lot_size", 1)
        self._refresh_chain()

    def _refresh_chain(self) -> None:
        self._selected_right = None
        self._selected_side = None
        self._selected_strike = None
        self._selected_premium = None
        self._selection_label.setText("No strike selected — click B or S on a Call/Put row below")
        self._chain_rows = []
        self._chain_table.setRowCount(0)
        columns = self._chain_columns()
        self._chain_table.setColumnCount(len(columns))
        self._chain_table.setHorizontalHeaderLabels(columns)

        underlying = self._underlying.currentText()
        expiry = self._expiry.currentData()
        if not underlying or expiry is None:
            return
        self._chain_rows = list(self._vm.leg_chain_strikes(underlying, expiry))
        if not self._chain_rows:
            self._show_error(self._vm.status_message or "No live strikes available")
            return
        self._error.setVisible(False)

        strike_col = self._strike_column()
        call_bs_col = self._call_bs_column()
        put_bs_col = self._put_bs_column()
        self._chain_table.setRowCount(len(self._chain_rows))
        for row, strike_row in enumerate(self._chain_rows):
            values = {strike_col: _fmt(strike_row.get("strike_price"))}
            if self._show_greeks:
                values[0] = _fmt(strike_row.get("call_delta"))
                values[2] = _fmt(strike_row.get("call_ltp"))
                values[3] = _fmt(strike_row.get("call_oi"))
                values[5] = _fmt(strike_row.get("put_oi"))
                values[6] = _fmt(strike_row.get("put_ltp"))
                values[8] = _fmt(strike_row.get("put_delta"))
            else:
                values[1] = _fmt(strike_row.get("call_ltp"))
                values[2] = _fmt(strike_row.get("call_oi"))
                values[4] = _fmt(strike_row.get("put_oi"))
                values[5] = _fmt(strike_row.get("put_ltp"))
            for col, text in values.items():
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._chain_table.setItem(row, col, item)

            if _to_decimal(strike_row.get("call_ltp")) is not None:
                self._chain_table.setCellWidget(row, call_bs_col, self._buy_sell_widget(row, "CE"))
            if _to_decimal(strike_row.get("put_ltp")) is not None:
                self._chain_table.setCellWidget(row, put_bs_col, self._buy_sell_widget(row, "PE"))

    def _buy_sell_widget(self, row: int, right: str) -> QWidget:
        """One row's Buy/Sell picker for a given side (Call or Put): two
        small buttons in a single cell -- clicking either immediately
        selects that strike/side/direction, replacing the separate Side
        dropdown this dialog used to have below the table."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(2)
        buy_btn = QToolButton()
        buy_btn.setText("B")
        buy_btn.setToolTip("Buy")
        sell_btn = QToolButton()
        sell_btn.setText("S")
        sell_btn.setToolTip("Sell")
        buy_btn.clicked.connect(partial(self._on_side_selected, row, right, "Buy"))
        sell_btn.clicked.connect(partial(self._on_side_selected, row, right, "Sell"))
        layout.addWidget(buy_btn)
        layout.addWidget(sell_btn)
        return container

    def _on_side_selected(self, row: int, right: str, side: str) -> None:
        if row >= len(self._chain_rows):
            return
        strike_row = self._chain_rows[row]
        strike = _to_decimal(strike_row.get("strike_price"))
        premium = _to_decimal(strike_row.get("call_ltp" if right == "CE" else "put_ltp"))
        if strike is None or premium is None:
            self._show_error(f"No live {right} quote for strike {_fmt(strike_row.get('strike_price'))}")
            return
        self._error.setVisible(False)
        self._selected_right = right
        self._selected_side = side
        self._selected_strike = strike
        self._selected_premium = premium
        self._chain_table.selectRow(row)
        self._selection_label.setText(f"Selected: {side} {right} {strike} @ {premium}")

    def _on_add(self) -> None:
        underlying = self._underlying.currentText()
        expiry = self._expiry.currentData()
        if not underlying or expiry is None:
            self._show_error("Select an underlying with an available expiry")
            return
        if (
            self._selected_right is None
            or self._selected_side is None
            or self._selected_strike is None
            or self._selected_premium is None
        ):
            self._show_error("Click Buy or Sell for a strike in the chain")
            return
        try:
            leg = build_leg_from_strike(
                underlying=underlying,
                exchange="NFO",
                expiry=expiry,
                right=self._selected_right,
                side=self._selected_side,
                lots=self._quantity.value(),
                strike=self._selected_strike,
                premium=self._selected_premium,
                lot_size=self._lot_size,
            )
        except ValueError as error:
            self._show_error(str(error))
            return
        self._vm.add_leg(leg)
        self.accept()

    def _show_error(self, message: str) -> None:
        self._error.setText(message)
        self._error.setVisible(True)
