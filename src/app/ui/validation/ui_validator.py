"""UI validation helpers."""

from PySide6.QtWidgets import QMessageBox, QWidget


class UIValidator:
    """Validate UI inputs before dispatching to application layer."""

    @staticmethod
    def require_text(value: str, field: str) -> bool:
        """Return True if text is non-empty."""
        return bool(value and value.strip())

    @staticmethod
    def show_error(parent: QWidget, title: str, message: str) -> None:
        """Show error dialog."""
        QMessageBox.warning(parent, title, message)
