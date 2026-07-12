"""Save strategy dialog placeholder."""

from PySide6.QtWidgets import QLineEdit, QWidget

from app.ui.dialogs.base_dialog import BaseDialog


class SaveDialog(BaseDialog):
    """Save resource dialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Save", "Enter save name:", parent)
        layout = self.layout()
        assert layout is not None
        self._input = QLineEdit()
        layout.insertWidget(1, self._input)

    def save_name(self) -> str:
        """Return entered save name."""
        return self._input.text().strip()
