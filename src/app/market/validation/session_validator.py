"""Trading session validator."""

from app.exceptions.validation_exception import ValidationException
from app.market.sessions.models import TradingSession


class SessionValidator:
    """Validate trading session records."""

    def validate(self, session: TradingSession) -> None:
        """Validate a trading session."""
        if not session.exchange.strip():
            raise ValidationException("exchange is required")
        if session.start_time >= session.end_time:
            raise ValidationException("start_time must be before end_time")
