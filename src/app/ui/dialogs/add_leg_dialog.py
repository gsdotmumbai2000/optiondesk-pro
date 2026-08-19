"""Add-leg dialog for the Strategy Builder."""

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                                 QLabel, QLineEdit, QSpinBox, QVBoxLayout, QWidget)

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


def build_leg_from_inputs(
    *,
    underlying: str,
    exchange: str,
    expiry: date,
    right: str,
    side: str,
    lots: int,
    strike_text: str,
    premium_text: str,
    lot_size: int,
) -> StrategyLeg:
    """Parse and validate raw form input into a StrategyLeg. Raises
    ValueError with a user-facing message on any invalid input -- a pure
    function so it's unit-testable without a Qt event loop."""
    kind = _KIND_BY_RIGHT_SIDE.get((right, side))
    if kind is None:
        raise ValueError(f"Unsupported right/side combination: {right}/{side}")
    if lots <= 0:
        raise ValueError("Quantity must be at least 1 lot")
    try:
        strike = Decimal(strike_text.strip())
    except InvalidOperation:
        raise ValueError("Strike must be a number") from None
    if strike <= 0:
        raise ValueError("Strike must be positive")
    try:
        premium = Decimal(premium_text.strip())
    except InvalidOperation:
        raise ValueError("Premium must be a number") from None
    if premium <= 0:
        raise ValueError("Premium must be positive")
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


class AddLegDialog(QDialog):
    """Collects one option leg's fields and adds it to the strategy
    currently being built, via TradingViewModel.add_leg()."""

    def __init__(self, view_model: TradingViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._lot_size = 1
        self.setWindowTitle("Add Leg")
        self.setMinimumWidth(360)

        self._underlying = QComboBox()
        self._underlying.addItems(self._vm.list_underlyings())
        self._expiry = QComboBox()
        self._right = QComboBox()
        self._right.addItems(("CE", "PE"))
        self._side = QComboBox()
        self._side.addItems(("Buy", "Sell"))
        self._quantity = QSpinBox()
        self._quantity.setRange(1, 10_000)
        self._quantity.setValue(1)
        self._strike = QLineEdit()
        self._premium = QLineEdit()
        self._error = QLabel()
        self._error.setStyleSheet("color: #d9534f;")
        self._error.setVisible(False)

        self._underlying.currentTextChanged.connect(self._refresh_expiries)
        self._refresh_expiries(self._underlying.currentText())

        form = QFormLayout()
        form.addRow("Underlying", self._underlying)
        form.addRow("Expiry", self._expiry)
        form.addRow("Right", self._right)
        form.addRow("Side", self._side)
        form.addRow("Quantity (lots)", self._quantity)
        form.addRow("Strike", self._strike)
        form.addRow("Premium", self._premium)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_add)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._error)
        layout.addWidget(buttons)

    def _refresh_expiries(self, underlying: str) -> None:
        self._expiry.clear()
        if not underlying:
            return
        context = self._vm.leg_builder_context(underlying)
        for label, expiry_date in context.get("expiries", []):
            self._expiry.addItem(label, expiry_date)
        self._lot_size = context.get("lot_size", 1)

    def _on_add(self) -> None:
        underlying = self._underlying.currentText()
        expiry = self._expiry.currentData()
        if not underlying or expiry is None:
            self._show_error("Select an underlying with an available expiry")
            return
        try:
            leg = build_leg_from_inputs(
                underlying=underlying,
                exchange="NFO",
                expiry=expiry,
                right=self._right.currentText(),
                side=self._side.currentText(),
                lots=self._quantity.value(),
                strike_text=self._strike.text(),
                premium_text=self._premium.text(),
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
