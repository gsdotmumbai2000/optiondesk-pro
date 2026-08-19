"""Backtest view."""

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.charts import pnl_chart
from app.ui.viewmodels.backtesting_viewmodel import BacktestingViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader

_TRADE_HEADERS = ("Time", "Symbol", "Side", "Qty", "Price", "Commission", "PnL")


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
        self._equity_chart = pnl_chart(title="Equity Curve")
        layout.addWidget(self._equity_chart)
        layout.addWidget(SectionHeader("Trade Log"))
        self._trades = DataTableWidget()
        self._trades_model = QStandardItemModel(0, len(_TRADE_HEADERS), self)
        self._trades_model.setHorizontalHeaderLabels(list(_TRADE_HEADERS))
        self._trades.setModel(self._trades_model)
        layout.addWidget(self._trades)
        layout.addWidget(SectionHeader("Performance Summary"))
        self._performance_summary = QLabel("Run a backtest to see performance metrics")
        layout.addWidget(self._performance_summary)
        viewmodel.result_changed.connect(self._on_result)

    def _on_result(self, result) -> None:
        """Render the latest run_command result (a BacktestResult) into the
        equity curve chart, trade log, and performance summary."""
        points = [(p.timestamp, p.equity) for p in result.equity_curve.points]
        self._equity_chart.set_series(points)

        self._trades_model.setRowCount(0)
        for trade in result.trade_log.trades:
            self._trades_model.appendRow([
                QStandardItem(str(trade.timestamp)),
                QStandardItem(trade.symbol),
                QStandardItem(trade.side.value),
                QStandardItem(str(trade.quantity)),
                QStandardItem(str(trade.price)),
                QStandardItem(str(trade.commission)),
                QStandardItem(str(trade.pnl)),
            ])

        self._performance_summary.setText(
            f"Total trades: {result.total_trades} | Win rate: {result.win_rate}% | "
            f"Net profit: {result.net_profit} | Max drawdown: {result.maximum_drawdown} | "
            f"Sharpe: {result.sharpe_ratio} | Profit factor: {result.profit_factor}"
        )
