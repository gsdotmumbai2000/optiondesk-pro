"""Strategy list table model (display only)."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

COLUMNS = ("Name", "Type", "Legs", "Updated")


class StrategyListTableModel(QAbstractTableModel):
    """Qt model for the saved-strategies list, backed by Strategy domain
    objects -- keeps each row's strategy_id alongside its display tuple so
    the view can map a selected row back to an id without touching the
    domain objects itself."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[str, ...]] = []
        self._strategy_ids: list[str] = []

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

    def set_strategies(self, strategies: list) -> None:
        """Load rows from a list/tuple of Strategy domain objects."""
        self.beginResetModel()
        self._strategy_ids = [strategy.strategy_id for strategy in strategies]
        self._rows = [
            (
                strategy.metadata.name,
                strategy.metadata.recognized_type.value,
                str(len(strategy.legs)),
                strategy.metadata.updated_at.strftime("%Y-%m-%d %H:%M")
                if strategy.metadata.updated_at
                else "—",
            )
            for strategy in strategies
        ]
        self.endResetModel()

    def strategy_id_for_row(self, row: int) -> str:
        """Return the strategy_id backing a given row, or '' if out of range."""
        if 0 <= row < len(self._strategy_ids):
            return self._strategy_ids[row]
        return ""
