"""Open strategy dialog placeholder."""

from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from app.ui.dialogs.base_dialog import BaseDialog


class OpenDialog(BaseDialog):
    """Open resource dialog (strategy/portfolio)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Open", "Enter resource identifier:", parent)
        layout = self.layout()
        assert layout is not None
        self._input = QLineEdit()
        layout.insertWidget(1, self._input)

    def resource_id(self) -> str:
        """Return entered resource id."""
        return self._input.text().strip()
