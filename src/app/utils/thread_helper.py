"""Threading utilities."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")


class ThreadHelper:
    """Helper for background thread execution."""

    def __init__(
        self, max_workers: int = 4, thread_name_prefix: str = "optiondesk"
    ) -> None:
        """Initialize the thread pool."""
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
        )

    def submit(self, func: Callable[[], T]) -> Future[T]:
        """Submit a callable to the thread pool."""
        return self._executor.submit(func)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the thread pool."""
        self._executor.shutdown(wait=wait, cancel_futures=False)
