"""Base application exception."""


class ApplicationException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
