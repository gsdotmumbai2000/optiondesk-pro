"""Tests for PortfolioView: positions/holdings tables must actually render
rows from positions_changed/holdings_changed, not just sit empty."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QPushButton

from app.ui.portfolio.portfolio_view import PortfolioView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


@dataclass(frozen=True, slots=True)
class _Position:
    symbol: str
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    status: SimpleNamespace
    unrealized_pnl: Decimal


@dataclass(frozen=True, slots=True)
class _Holding:
    symbol: str
    asset_class: SimpleNamespace
    quantity: int
    average_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal


def _position(symbol: str = "NIFTY24500CE") -> _Position:
    return _Position(
        symbol=symbol, quantity=50, entry_price=Decimal("120"), current_price=Decimal("135"),
        status=SimpleNamespace(value="OPEN"), unrealized_pnl=Decimal("750"),
    )


def _holding(symbol: str = "RELIANCE") -> _Holding:
    return _Holding(
        symbol=symbol, asset_class=SimpleNamespace(value="EQUITY"), quantity=10,
        average_price=Decimal("2800"), market_value=Decimal("29000"), unrealized_pnl=Decimal("1000"),
    )


class _FakeCommand:
    def __init__(self) -> None:
        self.executed = False

    def execute(self) -> None:
        self.executed = True


class _FakePortfolioViewModel(QObject):
    summary_changed = Signal(str)
    positions_changed = Signal(list)
    holdings_changed = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.refresh_command = _FakeCommand()
        self.export_command = _FakeCommand()


def _make_view(qapp: QApplication) -> tuple[PortfolioView, _FakePortfolioViewModel]:
    vm = _FakePortfolioViewModel()
    return PortfolioView(vm), vm


class TestPositionsTable:
    def test_positions_changed_populates_rows(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.positions_changed.emit([_position("A"), _position("B")])

        assert view._positions_model.rowCount() == 2
        assert view._positions_model.item(0, 0).text() == "A"

    def test_empty_positions_clears_table(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)
        vm.positions_changed.emit([_position("A")])

        vm.positions_changed.emit([])

        assert view._positions_model.rowCount() == 0

    def test_position_columns_reflect_fields(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.positions_changed.emit([_position("NIFTY24500CE")])

        row = [view._positions_model.item(0, c).text() for c in range(6)]
        assert row == ["NIFTY24500CE", "50", "120", "135", "OPEN", "750"]


class TestHoldingsTable:
    def test_holdings_changed_populates_rows(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.holdings_changed.emit([_holding("A"), _holding("B")])

        assert view._holdings_model.rowCount() == 2

    def test_empty_holdings_clears_table(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)
        vm.holdings_changed.emit([_holding("A")])

        vm.holdings_changed.emit([])

        assert view._holdings_model.rowCount() == 0


def _button(view: PortfolioView, label: str) -> QPushButton:
    return next(b for b in view.findChildren(QPushButton) if b.text() == label)


class TestRefreshAndExportButtonsAreWired:
    def test_clicking_refresh_button_executes_refresh_command(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        _button(view, "Refresh").click()

        assert vm.refresh_command.executed is True

    def test_clicking_export_button_executes_export_command(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        _button(view, "Export").click()

        assert vm.export_command.executed is True
