"""Main window ribbon toolbar."""

from PySide6.QtWidgets import QToolBar, QWidget

from app.ui.viewmodels.backtesting_viewmodel import BacktestingViewModel
from app.ui.viewmodels.trading_viewmodel import TradingViewModel


def build_ribbon(
    parent: QWidget,
    trading_vm: TradingViewModel,
    backtest_vm: BacktestingViewModel,
) -> QToolBar:
    """Build ribbon-style toolbar."""
    ribbon = QToolBar("Ribbon", parent)
    ribbon.setObjectName("mainRibbon")
    ribbon.setMovable(False)
    for label, cmd in (
        ("Open", trading_vm.load_command),
        ("Save", trading_vm.save_command),
        ("Refresh", trading_vm.refresh_command),
        ("Evaluate", trading_vm.evaluate_command),
        ("Optimize", trading_vm.optimize_command),
        ("Backtest", backtest_vm.run_command),
        ("AI", trading_vm.recommend_command),
    ):
        action = ribbon.addAction(label)
        if cmd is not None:
            action.triggered.connect(cmd.execute)
    return ribbon
