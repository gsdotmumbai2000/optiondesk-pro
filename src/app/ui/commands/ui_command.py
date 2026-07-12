"""UI relay command."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Signal


class RelayCommand(QObject):
    """MVVM command binding execute and can_execute."""

    can_execute_changed = Signal(bool)

    def __init__(
        self,
        execute: Callable[[], None],
        can_execute: Callable[[], bool] | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialize command."""
        super().__init__(parent)
        self._execute = execute
        self._can_execute = can_execute or (lambda: True)

    def execute(self) -> None:
        """Execute command if allowed."""
        if self.can_execute():
            self._execute()

    def can_execute(self) -> bool:
        """Return whether command can execute."""
        return self._can_execute()

    def raise_can_execute_changed(self) -> None:
        """Notify can_execute changed."""
        self.can_execute_changed.emit(self.can_execute())
