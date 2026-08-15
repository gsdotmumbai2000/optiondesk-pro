"""Market view."""

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from app.logging.logging_manager import get_logger
from app.ui.charts import price_chart, volatility_chart
from app.ui.option_chain.option_chain_view import OptionChainView
from app.ui.viewmodels.market_viewmodel import MarketViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader
from app.ui.widgets.live_price_widget import LivePriceWidget

_WATCHLIST_HEADERS = ("Symbol", "LTP", "Change", "Updated")
logger = get_logger(__name__)


class MarketView(QWidget):
    """Watchlist, indices, breadth, volatility, option chain."""

    def __init__(self, viewmodel: MarketViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        self._symbol_rows: dict[str, int] = {}
        layout = QVBoxLayout(self)
        self._spot = LivePriceWidget("NIFTY Spot")
        layout.addWidget(self._spot)
        top = QHBoxLayout()
        self._watchlist = DataTableWidget()
        self._watchlist_model = QStandardItemModel(0, len(_WATCHLIST_HEADERS), self)
        self._watchlist_model.setHorizontalHeaderLabels(list(_WATCHLIST_HEADERS))
        self._watchlist.setModel(self._watchlist_model)
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
        viewmodel.tick_updated.connect(self._on_tick)
        viewmodel.market_status_changed.connect(self._on_market_status)
        viewmodel.option_chain_changed.connect(self._chain.load_rows)
        self._on_watchlist(viewmodel.watchlist)

    def _wrap(self, title: str, widget: QWidget) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.addWidget(SectionHeader(title))
        v.addWidget(widget)
        return box

    def _on_watchlist(self, symbols: list) -> None:
        tooltip = ", ".join(symbols)
        self._watchlist.setToolTip(tooltip)
        self._indices.setToolTip(tooltip)
        self._watchlist_model.setRowCount(0)
        self._symbol_rows.clear()
        for symbol in symbols:
            row = self._watchlist_model.rowCount()
            self._watchlist_model.insertRow(row)
            self._watchlist_model.setItem(row, 0, QStandardItem(str(symbol)))
            for column in range(1, len(_WATCHLIST_HEADERS)):
                self._watchlist_model.setItem(row, column, QStandardItem("—"))
            self._symbol_rows[str(symbol)] = row

    def _on_tick(self, payload: dict) -> None:
        tick = payload.get("tick", payload)
        symbol = str(tick.get("symbol", ""))
        if symbol == "NIFTY":
            self._spot.update_tick(tick)
        logger.debug(
            "Watchlist tick lookup: incoming_symbol={incoming_symbol!r}, "
            "available_keys={available_keys!r}, lookup_result={lookup_result!r}",
            incoming_symbol=symbol,
            available_keys=list(self._symbol_rows),
            lookup_result=self._symbol_rows.get(symbol),
        )
        row = self._symbol_rows.get(symbol)
        if row is None:
            return
        self._watchlist_model.setItem(row, 1, QStandardItem(str(tick.get("ltp", "—"))))
        self._watchlist_model.setItem(row, 2, QStandardItem(str(tick.get("change", "—"))))
        self._watchlist_model.setItem(row, 3, QStandardItem(str(tick.get("timestamp", "—"))))

    def _on_market_status(self, payload: dict) -> None:
        status = str(payload.get("status", "—"))
        self._spot.set_market_status(f"Market: {status}")
