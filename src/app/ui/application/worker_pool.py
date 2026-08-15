"""Background worker for non-blocking UI operations."""

import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, QRunnable, QThreadPool, Qt, Signal, Slot

from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class WorkerSignals(QObject):
    """Signals for worker completion.

    `finished`/`error` are emitted from a QThreadPool worker thread (see
    WorkerRunnable.run). Qt can only auto-marshal an emit to the GUI thread
    when the connected slot belongs to a QObject with known thread affinity;
    a plain Python closure has no such affinity, so connecting directly to
    one collapses to a same-thread DirectConnection and the closure runs on
    the emitting worker thread instead of the GUI thread.

    When constructed with `on_finished`/`on_error`, this object connects its
    own signals to its own bound `_deliver_*` slots with an explicit
    QueuedConnection. Because `self` is a real QObject constructed on the
    GUI thread (every current call site constructs `WorkerSignals` from a Qt
    slot handler running on the GUI thread) and parented to the
    QCoreApplication singleton (guaranteed alive and GUI-thread-affine for
    the app's lifetime), Qt has a provable, real GUI-thread receiver to
    queue the callback onto -- the external callback then runs on the GUI
    thread when Qt delivers that queued event.

    Constructing with no callbacks (`WorkerSignals()`) leaves `finished`/
    `error` as plain signals callers may `.connect()` to directly, unchanged
    from prior behavior (used by existing same-thread WorkerRunnable tests).
    """

    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        on_finished: Callable[[Any], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialize signals, optionally self-wiring GUI-thread delivery."""
        super().__init__(parent)
        self._on_finished = on_finished
        self._on_error = on_error
        if on_finished is not None:
            self.finished.connect(
                self._deliver_finished, Qt.ConnectionType.QueuedConnection
            )
        if on_error is not None:
            self.error.connect(self._deliver_error, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _deliver_finished(self, result: Any) -> None:
        """Run the caller's on_finished callback on this object's (GUI) thread."""
        try:
            assert self._on_finished is not None
            self._on_finished(result)
        except Exception:
            logger.exception("BackgroundWorker: on_finished callback raised")
        finally:
            self.deleteLater()

    @Slot(str)
    def _deliver_error(self, message: str) -> None:
        """Run the caller's on_error callback on this object's (GUI) thread."""
        try:
            assert self._on_error is not None
            self._on_error(message)
        except Exception:
            logger.exception("BackgroundWorker: on_error callback raised")
        finally:
            self.deleteLater()


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
        """Run function in background.

        `on_finished`/`on_error` are guaranteed to execute on the GUI/main
        Qt thread, regardless of which QThreadPool worker thread `fn` runs
        on -- see WorkerSignals for how that delivery is marshaled.
        """
        signals = WorkerSignals(on_finished, on_error, parent=QCoreApplication.instance())
        logger.debug(
            "BackgroundWorker.run: dispatching to pool active={active} max={max}",
            active=self._pool.activeThreadCount(),
            max=self._pool.maxThreadCount(),
        )
        self._pool.start(WorkerRunnable(fn, signals))
