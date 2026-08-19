"""Open resource dialog (strategy/portfolio): picks one id from a list of
real (id, name) pairs the caller already fetched -- e.g. from
TradingViewModel.list_strategies() -- rather than asking the user to type
a blind id into a text box."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from app.ui.dialogs.base_dialog import BaseDialog


class OpenDialog(BaseDialog):
    """Pick one resource from a list of (id, name) pairs."""

    def __init__(self, items: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__("Open", "Select an item to load:", parent)
        layout = self.layout()
        assert layout is not None
        self._list = QListWidget()
        for item_id, name in items:
            entry = QListWidgetItem(name or item_id)
            entry.setData(Qt.ItemDataRole.UserRole, item_id)
            self._list.addItem(entry)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        layout.insertWidget(1, self._list)

    def selected_id(self) -> str:
        """Return the id of the selected item, or "" if none selected
        (empty list, or the user cleared the selection)."""
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else ""
