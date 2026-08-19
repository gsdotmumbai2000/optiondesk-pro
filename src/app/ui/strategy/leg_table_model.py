"""Strategy leg table model (display only) for the Strategy Builder's
in-progress, not-yet-saved leg list."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg

COLUMNS = ("Side", "Right", "Strike", "Expiry", "Qty (lots)", "Premium")

_RIGHT_BY_KIND = {
    LegKind.CALL_BUY: "CE",
    LegKind.CALL_SELL: "CE",
    LegKind.PUT_BUY: "PE",
    LegKind.PUT_SELL: "PE",
    LegKind.FUTURE_BUY: "FUT",
    LegKind.FUTURE_SELL: "FUT",
    LegKind.STOCK_BUY: "STK",
    LegKind.STOCK_SELL: "STK",
}


class StrategyLegTableModel(QAbstractTableModel):
    """Qt model for the strategy builder's pending legs, backed by
    StrategyLeg domain objects -- keeps each row's leg_id alongside its
    display tuple so the view can map a selected row back to an id without
    touching the domain objects itself."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[str, ...]] = []
        self._leg_ids: list[str] = []

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

    def set_legs(self, legs: list[StrategyLeg]) -> None:
        """Load rows from a list/tuple of StrategyLeg domain objects."""
        self.beginResetModel()
        self._leg_ids = [leg.leg_id for leg in legs]
        self._rows = [
            (
                "Sell" if leg.kind.value.endswith("SELL") else "Buy",
                _RIGHT_BY_KIND.get(leg.kind, "—"),
                str(leg.strike),
                leg.expiry.isoformat() if leg.expiry else "—",
                str(leg.quantity),
                str(leg.premium),
            )
            for leg in legs
        ]
        self.endResetModel()

    def leg_id_for_row(self, row: int) -> str:
        """Return the leg_id backing a given row, or '' if out of range."""
        if 0 <= row < len(self._leg_ids):
            return self._leg_ids[row]
        return ""
