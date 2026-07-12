"""Base ViewModel for MVVM."""

from PySide6.QtCore import QObject, Property, Signal


class BaseViewModel(QObject):
    """Base class for all ViewModels."""

    busy_changed = Signal(bool)
    status_message_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize view model."""
        super().__init__(parent)
        self._busy = False
        self._status_message = ""

    @Property(bool, notify=busy_changed)
    def busy(self) -> bool:
        """Return busy state."""
        return self._busy

    @busy.setter
    def busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busy_changed.emit(value)

    @Property(str, notify=status_message_changed)
    def status_message(self) -> str:
        """Return status message."""
        return self._status_message

    @status_message.setter
    def status_message(self, value: str) -> None:
        if self._status_message != value:
            self._status_message = value
            self.status_message_changed.emit(value)

    def set_error(self, message: str) -> None:
        """Emit error signal."""
        self.error_occurred.emit(message)
