"""Market view."""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from app.ui.charts import price_chart, volatility_chart
from app.ui.option_chain.option_chain_view import OptionChainView
from app.ui.viewmodels.market_viewmodel import MarketViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class MarketView(QWidget):
    """Watchlist, indices, breadth, volatility, option chain."""

    def __init__(self, viewmodel: MarketViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self._watchlist = DataTableWidget()
        self._indices = DataTableWidget()
        top.addWidget(self._wrap("Watchlist", self._watchlist))
        top.addWidget(self._wrap("Indices", self._indices))
        layout.addLayout(top)
        mid = QHBoxLayout()
        mid.addWidget(volatility_chart())
        mid.addWidget(price_chart())
        layout.addLayout(mid)
        self._chain = OptionChainView()
        layout.addWidget(self._chain)
        viewmodel.watchlist_changed.connect(self._on_watchlist)

    def _wrap(self, title: str, widget: QWidget) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.addWidget(SectionHeader(title))
        v.addWidget(widget)
        return box

    def _on_watchlist(self, symbols: list) -> None:
        self._watchlist.setToolTip(", ".join(symbols))
