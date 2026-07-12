"""Global exception handler."""

import sys
import traceback
from collections.abc import Callable
from types import TracebackType

from app.exceptions.application_exception import ApplicationException
from app.logging.logging_manager import LoggingManager, get_logger

ExceptionHook = Callable[
    [type[BaseException], BaseException, TracebackType | None], None
]


class GlobalExceptionHandler:
    """Install and manage global uncaught exception handling."""

    def __init__(self, logging_manager: LoggingManager) -> None:
        """Initialize the handler."""
        self._logging_manager = logging_manager
        self._logger = get_logger(__name__)
        self._previous_hook: ExceptionHook | None = None
        self._installed = False

    def install(self) -> None:
        """Install the global exception hook."""
        if self._installed:
            return
        self._previous_hook = sys.excepthook
        sys.excepthook = self._handle_exception
        self._installed = True
        self._logger.info("Global exception handler installed")

    def uninstall(self) -> None:
        """Restore the previous exception hook."""
        if not self._installed:
            return
        if self._previous_hook is not None:
            sys.excepthook = self._previous_hook
        self._installed = False
        self._logger.info("Global exception handler uninstalled")

    def _handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            if self._previous_hook is not None:
                self._previous_hook(exc_type, exc_value, exc_traceback)
            return

        formatted = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        if isinstance(exc_value, ApplicationException):
            self._logger.error(
                "Unhandled application exception [{code}]: {message}",
                code=exc_value.code,
                message=exc_value.message,
            )
        else:
            self._logger.critical("Unhandled exception: {error}", error=exc_value)

        self._logging_manager.log_crash_report(
            exception_type=exc_type.__name__,
            exception_message=str(exc_value),
            stack_trace=formatted,
        )

        if self._previous_hook is not None:
            self._previous_hook(exc_type, exc_value, exc_traceback)
