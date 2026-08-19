"""Tests for BacktestView: the trade log table and performance summary must
actually render real BacktestResult data, not just sit empty."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.ui.backtesting.backtest_view import BacktestView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


@dataclass(frozen=True, slots=True)
class _Trade:
    timestamp: datetime
    symbol: str
    side: SimpleNamespace
    quantity: int
    price: Decimal
    commission: Decimal
    pnl: Decimal


def _trade(symbol: str = "NIFTY24500CE") -> _Trade:
    return _Trade(
        timestamp=datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc), symbol=symbol,
        side=SimpleNamespace(value="BUY"), quantity=50, price=Decimal("120"),
        commission=Decimal("20"), pnl=Decimal("500"),
    )


def _result(trades: tuple = ()) -> SimpleNamespace:
    return SimpleNamespace(
        equity_curve=SimpleNamespace(points=()),
        trade_log=SimpleNamespace(trades=trades),
        total_trades=len(trades),
        win_rate=Decimal("60"),
        net_profit=Decimal("5000"),
        maximum_drawdown=Decimal("800"),
        sharpe_ratio=Decimal("1.5"),
        profit_factor=Decimal("2.1"),
    )


class _FakeCommand:
    def execute(self) -> None:
        pass


class _FakeBacktestingViewModel(QObject):
    run_state_changed = Signal(str)
    result_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.run_command = _FakeCommand()
        self.pause_command = _FakeCommand()
        self.resume_command = _FakeCommand()
        self.stop_command = _FakeCommand()
        self.export_command = _FakeCommand()


def _make_view(qapp: QApplication) -> tuple[BacktestView, _FakeBacktestingViewModel]:
    vm = _FakeBacktestingViewModel()
    return BacktestView(vm), vm


class TestTradeLogTable:
    def test_result_changed_populates_trade_rows(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.result_changed.emit(_result((_trade("A"), _trade("B"))))

        assert view._trades_model.rowCount() == 2
        assert view._trades_model.item(0, 1).text() == "A"

    def test_empty_trade_log_clears_table(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)
        vm.result_changed.emit(_result((_trade("A"),)))

        vm.result_changed.emit(_result(()))

        assert view._trades_model.rowCount() == 0


class TestPerformanceSummary:
    def test_result_changed_renders_key_metrics(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.result_changed.emit(_result((_trade(),)))

        text = view._performance_summary.text()
        assert "Total trades: 1" in text
        assert "Win rate: 60%" in text
        assert "Net profit: 5000" in text
