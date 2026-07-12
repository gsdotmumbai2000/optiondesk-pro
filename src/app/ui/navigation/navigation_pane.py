"""Navigation pane."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QVBoxLayout, QWidget

from app.ui.models.ui_enums import UIWorkspaceId


class NavigationPane(QWidget):
    """Left navigation pane for workspace switching."""

    workspace_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(160)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        self._list = QListWidget()
        for ws in UIWorkspaceId:
            self._list.addItem(ws.value.replace("_", " ").title())
        self._list.currentRowChanged.connect(self._on_row)
        layout.addWidget(self._list)
        self._list.setCurrentRow(0)

    def _on_row(self, row: int) -> None:
        items = list(UIWorkspaceId)
        if 0 <= row < len(items):
            self.workspace_selected.emit(items[row].value)
