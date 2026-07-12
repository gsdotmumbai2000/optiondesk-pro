"""Retry utilities."""

import time
from collections.abc import Callable
from typing import TypeVar

from loguru import logger

T = TypeVar("T")


class RetryHelper:
    """Helper for retrying transient operations."""

    @staticmethod
    def retry(
        operation: Callable[[], T],
        *,
        max_attempts: int = 3,
        delay_seconds: float = 1.0,
        backoff_multiplier: float = 2.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> T:
        """Execute an operation with exponential backoff retries."""
        attempt = 1
        current_delay = delay_seconds
        last_error: Exception | None = None

        while attempt <= max_attempts:
            try:
                return operation()
            except exceptions as error:
                last_error = error
                logger.warning(
                    "Retry attempt {attempt}/{max_attempts} failed: {error}",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                )
                if attempt == max_attempts:
                    break
                time.sleep(current_delay)
                current_delay *= backoff_multiplier
                attempt += 1

        assert last_error is not None
        raise last_error
