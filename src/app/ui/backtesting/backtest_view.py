"""Backtest view."""

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.ui.charts import pnl_chart
from app.ui.viewmodels.backtesting_viewmodel import BacktestingViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class BacktestView(QWidget):
    """Replay controls, equity curve, trade log, performance."""

    def __init__(self, viewmodel: BacktestingViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        for label, cmd in (
            ("Run", viewmodel.run_command),
            ("Pause", viewmodel.pause_command),
            ("Resume", viewmodel.resume_command),
            ("Stop", viewmodel.stop_command),
            ("Export", viewmodel.export_command),
        ):
            b = QPushButton(label)
            b.clicked.connect(cmd.execute)
            controls.addWidget(b)
        layout.addLayout(controls)
        # Ready for viewmodel.run_command's BacktestResult.equity_curve via
        # self._equity_chart.set_series() once that command runs a real
        # BacktestRequest instead of its current placeholder.
        self._equity_chart = pnl_chart(title="Equity Curve")
        layout.addWidget(self._equity_chart)
        layout.addWidget(SectionHeader("Trade Log"))
        self._trades = DataTableWidget()
        layout.addWidget(self._trades)
        layout.addWidget(SectionHeader("Performance Summary"))
