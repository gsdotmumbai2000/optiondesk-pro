"""Option chain view (UI only)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.ui.option_chain.chain_model import OptionChainTableModel
from app.ui.widgets.common import DataTableWidget, SectionHeader

_CHAIN_WIDTHS = (5, 10, 20, 30)
_DEFAULT_CHAIN_WIDTH = 10


class OptionChainView(QWidget):
    """Display calls/puts chain with filter, sort, expiry, and strike-width control."""

    chain_width_changed = Signal(int)
    expiry_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Option Chain"))
        filter_row = QHBoxLayout()
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter by strike...")
        self._filter.textChanged.connect(self._on_filter)
        filter_row.addWidget(self._filter)
        filter_row.addWidget(QLabel("Expiry:"))
        self._expiry = QComboBox()
        self._expiry.currentIndexChanged.connect(self._on_expiry_changed)
        filter_row.addWidget(self._expiry)
        filter_row.addWidget(QLabel("Strikes:"))
        self._width = QComboBox()
        for radius in _CHAIN_WIDTHS:
            self._width.addItem(f"ATM ±{radius}", radius)
        self._width.setCurrentIndex(_CHAIN_WIDTHS.index(_DEFAULT_CHAIN_WIDTH))
        self._width.currentIndexChanged.connect(self._on_width_changed)
        filter_row.addWidget(self._width)
        layout.addLayout(filter_row)
        self._model = OptionChainTableModel(self)
        self._table = DataTableWidget(self)
        self._table.setModel(self._model)
        layout.addWidget(self._table)

    def load_rows(self, rows: list[tuple[str, ...]]) -> None:
        """Load rows from application services."""
        self._model.set_placeholder_rows(rows)

    def set_expiries(self, items: list[tuple[str, str]]) -> None:
        """Populate the expiry dropdown: items = [(label, expiry_date), ...].

        Preserves the current selection (by expiry_date value) across a
        repopulate, and never fires expiry_changed as a side effect of
        this -- only a direct user selection should trigger a reload.
        """
        current = self._expiry.currentData()
        self._expiry.blockSignals(True)
        self._expiry.clear()
        for label, expiry_date in items:
            self._expiry.addItem(label, expiry_date)
        if current is not None:
            index = self._expiry.findData(current)
            if index >= 0:
                self._expiry.setCurrentIndex(index)
        self._expiry.blockSignals(False)

    def set_selected_expiry(self, expiry_date: str) -> None:
        """Reflect the expiry actually loaded (may differ from the user's
        pending click, e.g. the initial auto-selected nearest expiry)
        without re-firing expiry_changed."""
        index = self._expiry.findData(expiry_date)
        if index < 0 or index == self._expiry.currentIndex():
            return
        self._expiry.blockSignals(True)
        self._expiry.setCurrentIndex(index)
        self._expiry.blockSignals(False)

    def _on_filter(self, text: str) -> None:
        self._model.filter_rows(text)

    def _on_width_changed(self, index: int) -> None:
        radius = self._width.itemData(index)
        if radius is not None:
            self.chain_width_changed.emit(int(radius))

    def _on_expiry_changed(self, index: int) -> None:
        expiry_date = self._expiry.itemData(index)
        if expiry_date:
            self.expiry_changed.emit(str(expiry_date))
