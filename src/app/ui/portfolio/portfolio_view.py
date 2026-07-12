"""Portfolio view."""

from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from app.ui.charts import pnl_chart
from app.ui.viewmodels.portfolio_viewmodel import PortfolioViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class PortfolioView(QWidget):
    """Positions, holdings, PnL, margin, risk, allocation."""

    def __init__(self, viewmodel: PortfolioViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Portfolio"))
        grid = QGridLayout()
        self._positions = DataTableWidget()
        self._holdings = DataTableWidget()
        grid.addWidget(self._positions, 0, 0)
        grid.addWidget(self._holdings, 0, 1)
        layout.addLayout(grid)
        layout.addWidget(pnl_chart())
        metrics = QGridLayout()
        for i, title in enumerate(("PnL", "Margin", "Risk", "Allocation")):
            metrics.addWidget(SectionHeader(title), 0, i)
        layout.addLayout(metrics)
        viewmodel.summary_changed.connect(lambda s: self._positions.setToolTip(s))
