"""Tick integrity validation."""

from datetime import datetime, timezone

from app.live.exceptions import LiveValidationException
from app.market_data.models.tick import TickSnapshot


class TickValidator:
    """Validate incoming market ticks."""

    def validate(self, tick: TickSnapshot) -> None:
        if not tick.symbol.strip():
            raise LiveValidationException("Tick symbol is required")
        if not tick.exchange.strip():
            raise LiveValidationException("Tick exchange is required")
        if tick.timestamp is not None and tick.timestamp > datetime.now(timezone.utc):
            raise LiveValidationException("Tick timestamp is in the future")
