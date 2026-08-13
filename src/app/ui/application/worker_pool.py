"""Background worker for non-blocking UI operations."""

import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


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
        pool = QThreadPool.globalInstance()
        logger.debug(
            "WorkerRunnable.run: starting on thread={thread} active={active} max={max}",
            thread=threading.current_thread().name,
            active=pool.activeThreadCount(),
            max=pool.maxThreadCount(),
        )
        try:
            result = self._fn()
            logger.debug("WorkerRunnable.run: fn() returned, emitting finished")
            self._signals.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - surface to UI
            logger.exception(
                "WorkerRunnable.run: fn() raised {exc_type}: {exc_message!r} "
                "(str(exc)={str_exc!r}, args={exc_args!r})",
                exc_type=type(exc).__name__,
                exc_message=repr(exc),
                str_exc=str(exc),
                exc_args=exc.args,
            )
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
        logger.debug(
            "BackgroundWorker.run: dispatching to pool active={active} max={max}",
            active=self._pool.activeThreadCount(),
            max=self._pool.maxThreadCount(),
        )
        self._pool.start(WorkerRunnable(fn, signals))
