"""Portfolio view."""

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.ui.charts import pnl_chart
from app.ui.viewmodels.portfolio_viewmodel import PortfolioViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader

_POSITION_HEADERS = ("Symbol", "Qty", "Entry Price", "Current Price", "Status", "Unrealized PnL")
_HOLDING_HEADERS = ("Symbol", "Asset Class", "Qty", "Avg Price", "Market Value", "Unrealized PnL")


class PortfolioView(QWidget):
    """Positions, holdings, PnL, margin, risk, allocation."""

    def __init__(self, viewmodel: PortfolioViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Portfolio"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(viewmodel.refresh_command.execute)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(viewmodel.export_command.execute)
        header_row.addWidget(refresh_btn)
        header_row.addWidget(export_btn)
        layout.addLayout(header_row)

        grid = QGridLayout()
        grid.addWidget(SectionHeader("Positions"), 0, 0)
        grid.addWidget(SectionHeader("Holdings"), 0, 1)
        self._positions = DataTableWidget()
        self._positions_model = QStandardItemModel(0, len(_POSITION_HEADERS), self)
        self._positions_model.setHorizontalHeaderLabels(list(_POSITION_HEADERS))
        self._positions.setModel(self._positions_model)
        self._holdings = DataTableWidget()
        self._holdings_model = QStandardItemModel(0, len(_HOLDING_HEADERS), self)
        self._holdings_model.setHorizontalHeaderLabels(list(_HOLDING_HEADERS))
        self._holdings.setModel(self._holdings_model)
        grid.addWidget(self._positions, 1, 0)
        grid.addWidget(self._holdings, 1, 1)
        layout.addLayout(grid)
        # Ready for real portfolio PnL history via self._pnl_chart.set_series()
        # once PortfolioViewModel exposes it (currently only a text summary).
        self._pnl_chart = pnl_chart(title="Portfolio PnL")
        layout.addWidget(self._pnl_chart)
        metrics = QGridLayout()
        for i, title in enumerate(("PnL", "Margin", "Risk", "Allocation")):
            metrics.addWidget(SectionHeader(title), 0, i)
        layout.addLayout(metrics)
        viewmodel.summary_changed.connect(lambda s: self._positions.setToolTip(s))
        viewmodel.positions_changed.connect(self._on_positions)
        viewmodel.holdings_changed.connect(self._on_holdings)

    def _on_positions(self, positions: list) -> None:
        self._positions_model.setRowCount(0)
        for position in positions:
            self._positions_model.appendRow([
                QStandardItem(position.symbol),
                QStandardItem(str(position.quantity)),
                QStandardItem(str(position.entry_price)),
                QStandardItem(str(position.current_price)),
                QStandardItem(position.status.value),
                QStandardItem(str(position.unrealized_pnl)),
            ])

    def _on_holdings(self, holdings: list) -> None:
        self._holdings_model.setRowCount(0)
        for holding in holdings:
            self._holdings_model.appendRow([
                QStandardItem(holding.symbol),
                QStandardItem(holding.asset_class.value),
                QStandardItem(str(holding.quantity)),
                QStandardItem(str(holding.average_price)),
                QStandardItem(str(holding.market_value)),
                QStandardItem(str(holding.unrealized_pnl)),
            ])
