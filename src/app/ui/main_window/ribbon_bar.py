"""Main window ribbon toolbar."""

from PySide6.QtWidgets import QDialog, QToolBar, QWidget

from app.ui.dialogs import OpenDialog, SaveDialog
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

    def _on_open() -> None:
        """Show a picker of saved strategies and load the selected one
        into the builder (mirrors the Strategy Builder view's own Load
        button -- this is the ribbon's global shortcut to the same flow)."""
        dialog = OpenDialog(trading_vm.list_strategies(), parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trading_vm.load_strategy(dialog.selected_id())

    def _on_save() -> None:
        """Prompt for a name and persist the strategy currently being built
        (save_new_strategy already no-ops with a status message if there are
        no pending legs, so no need to check here)."""
        dialog = SaveDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trading_vm.save_new_strategy(dialog.save_name())

    for label, cmd in (
        ("Open", None),
        ("Save", None),
        ("Refresh", trading_vm.refresh_command),
        ("Evaluate", trading_vm.evaluate_command),
        ("Refresh Margin", trading_vm.refresh_margin_command),
        ("Optimize", trading_vm.optimize_command),
        ("Backtest", backtest_vm.run_command),
        ("AI", trading_vm.recommend_command),
    ):
        action = ribbon.addAction(label)
        if label == "Open":
            action.triggered.connect(_on_open)
        elif label == "Save":
            action.triggered.connect(_on_save)
        elif cmd is not None:
            action.triggered.connect(cmd.execute)
    return ribbon
