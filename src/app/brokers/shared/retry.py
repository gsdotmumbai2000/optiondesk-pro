"""Retry helpers for broker operations."""

import time
from collections.abc import Callable
from typing import TypeVar

from app.brokers.shared.exceptions import (BrokerRateLimitException,
                                           BrokerTimeoutException)

T = TypeVar("T")


def retry_call(
    func: Callable[[], T],
    *,
    max_retries: int = 3,
    backoff_ms: int = 500,
    retry_on: tuple[type[Exception], ...] = (
        BrokerTimeoutException,
        BrokerRateLimitException,
    ),
) -> T:
    """Execute a callable with exponential backoff retries."""
    attempt = 0
    while True:
        try:
            return func()
        except retry_on:
            attempt += 1
            if attempt > max_retries:
                raise
            time.sleep((backoff_ms * attempt) / 1000)
