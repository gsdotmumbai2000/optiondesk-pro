"""Background worker for non-blocking UI operations."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class WorkerSignals(QObject):
    """Signals for worker completion."""

    finished = Signal(object)
    error = Signal(str)


class WorkerRunnable(QRunnable):
    """Run callable on thread pool."""

    def __init__(self, fn: Callable[[], Any], signals: WorkerSignals) -> None:
        """Initialize runnable."""
        super().__init__()
        self._fn = fn
        self._signals = signals

    @Slot()
    def run(self) -> None:
        """Execute work."""
        try:
            result = self._fn()
            self._signals.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - surface to UI
            self._signals.error.emit(str(exc))


class BackgroundWorker:
    """Dispatch work to QThreadPool."""

    def __init__(self) -> None:
        """Initialize worker pool."""
        self._pool = QThreadPool.globalInstance()

    def run(
        self,
        fn: Callable[[], Any],
        on_finished: Callable[[Any], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Run function in background."""
        signals = WorkerSignals()
        signals.finished.connect(on_finished)
        signals.error.connect(on_error)
        self._pool.start(WorkerRunnable(fn, signals))
