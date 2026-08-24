"""Open resource dialog (strategy/portfolio): picks one id from a list of
real (id, name) pairs the caller already fetched -- e.g. from
TradingViewModel.list_strategies() -- rather than asking the user to type
a blind id into a text box."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QWidget

from app.ui.dialogs.base_dialog import BaseDialog


class OpenDialog(BaseDialog):
    """Pick one resource from a list of (id, name) pairs."""

    def __init__(
        self,
        items: list[tuple[str, str]],
        parent: QWidget | None = None,
        on_delete: Callable[[str], bool] | None = None,
    ) -> None:
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

        self._on_delete = on_delete
        if on_delete is not None:
            delete_row = QHBoxLayout()
            delete_row.addStretch(1)
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(self._delete_selected)
            delete_row.addWidget(delete_btn)
            layout.insertLayout(2, delete_row)

    def selected_id(self) -> str:
        """Return the id of the selected item, or "" if none selected
        (empty list, or the user cleared the selection)."""
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else ""

    def _delete_selected(self) -> None:
        """Delete the selected item via the caller's on_delete callback,
        after confirmation, and drop its row from the list on success --
        the dialog stays open so the user can delete several in a row."""
        item = self._list.currentItem()
        if item is None:
            return
        item_id = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()
        confirm = QMessageBox.question(
            self,
            "Delete",
            f'Delete "{name}"? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        assert self._on_delete is not None
        if self._on_delete(item_id):
            self._list.takeItem(self._list.row(item))
        else:
            QMessageBox.warning(self, "Delete", f'Could not delete "{name}".')
