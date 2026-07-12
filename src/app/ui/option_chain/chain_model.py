"""Option chain table model (display only)."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


COLUMNS = ("Type", "Strike", "OI", "Volume", "IV", "Delta", "Gamma", "Theta", "Vega")


class OptionChainTableModel(QAbstractTableModel):
    """Qt model for option chain rows (placeholder data)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[str, ...]] = []
        self._all_rows: list[tuple[str, ...]] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._rows[index.row()][index.column()]

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section]
        return section + 1

    def set_placeholder_rows(self, rows: list[tuple[str, ...]]) -> None:
        """Load display rows from application layer (no calculations)."""
        self.beginResetModel()
        self._all_rows = list(rows)
        self._rows = list(rows)
        self.endResetModel()

    def filter_rows(self, text: str) -> None:
        """Filter by strike symbol substring."""
        self.beginResetModel()
        if not text:
            self._rows = list(self._all_rows)
        else:
            self._rows = [r for r in self._all_rows if text.lower() in str(r[1]).lower()]
        self.endResetModel()
