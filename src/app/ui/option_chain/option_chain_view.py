"""Option chain view (UI only)."""

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from app.ui.option_chain.chain_model import OptionChainTableModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class OptionChainView(QWidget):
    """Display calls/puts chain with filter and sort."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Option Chain"))
        filter_row = QHBoxLayout()
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter by strike...")
        self._filter.textChanged.connect(self._on_filter)
        filter_row.addWidget(self._filter)
        layout.addLayout(filter_row)
        self._model = OptionChainTableModel(self)
        self._table = DataTableWidget(self)
        self._table.setModel(self._model)
        layout.addWidget(self._table)

    def load_rows(self, rows: list[tuple[str, ...]]) -> None:
        """Load rows from application services."""
        self._model.set_placeholder_rows(rows)

    def _on_filter(self, text: str) -> None:
        self._model.filter_rows(text)
