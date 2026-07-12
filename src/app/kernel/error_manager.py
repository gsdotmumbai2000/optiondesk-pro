"""Centralized error management."""

from collections.abc import Callable

from app.exceptions.application_exception import ApplicationException
from app.logging.logging_manager import LoggingManager, get_logger

logger = get_logger(__name__)
RecoveryAction = Callable[[], None]


class ErrorManager:
    """Classify, log, and recover from application errors."""

    def __init__(self, logging_manager: LoggingManager) -> None:
        """Initialize the error manager."""
        self._logging_manager = logging_manager

    def handle(
        self,
        error: Exception,
        *,
        context: str,
        recovery: RecoveryAction | None = None,
        friendly_message: str | None = None,
    ) -> str:
        """Handle an error and return a user-friendly message."""
        if isinstance(error, ApplicationException):
            logger.error("[{code}] {message}", code=error.code, message=error.message)
            message = friendly_message or error.message
        else:
            logger.exception(
                "Unexpected error in {context}: {error}", context=context, error=error
            )
            message = (
                friendly_message or "An unexpected error occurred. Please try again."
            )

        if recovery is not None:
            try:
                recovery()
            except Exception as recovery_error:
                logger.error("Recovery failed: {error}", error=recovery_error)

        return message

    def handle_with_retry(
        self,
        operation: Callable[[], None],
        *,
        context: str,
        max_attempts: int = 3,
    ) -> None:
        """Execute an operation with retry handling."""
        attempt = 0
        last_error: Exception | None = None
        while attempt < max_attempts:
            try:
                operation()
                return
            except Exception as error:
                last_error = error
                attempt += 1
                self.handle(error, context=f"{context} (attempt {attempt})")
        if last_error is not None:
            raise last_error
