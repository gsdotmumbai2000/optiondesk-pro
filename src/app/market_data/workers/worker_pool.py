"""Background worker pool."""

from collections import deque
from collections.abc import Callable
from threading import Event, RLock, Thread
from typing import TypeVar

from app.logging.logging_manager import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class WorkerPool:
    """Process queued tasks on background threads."""

    def __init__(self, name: str, *, workers: int = 1) -> None:
        """Initialize worker pool."""
        self._name = name
        self._queue: deque[Callable[[], None]] = deque()
        self._lock = RLock()
        self._stop_event = Event()
        self._threads = [
            Thread(target=self._run, name=f"{name}-worker-{index}", daemon=True)
            for index in range(workers)
        ]

    def start(self) -> None:
        """Start worker threads."""
        self._stop_event.clear()
        for thread in self._threads:
            if not thread.is_alive():
                thread.start()

    def stop(self) -> None:
        """Stop worker threads."""
        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=2)

    def submit(self, task: Callable[[], None]) -> None:
        """Enqueue a task."""
        with self._lock:
            self._queue.append(task)

    def pending(self) -> int:
        """Return pending task count."""
        with self._lock:
            return len(self._queue)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            task: Callable[[], None] | None = None
            with self._lock:
                if self._queue:
                    task = self._queue.popleft()
            if task is None:
                self._stop_event.wait(0.05)
                continue
            try:
                task()
            except Exception as error:
                logger.warning(
                    "Worker {name} task failed: {error}",
                    name=self._name,
                    error=error,
                )
