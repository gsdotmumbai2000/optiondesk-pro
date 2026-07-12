"""Trading session models."""

from datetime import time

from pydantic import BaseModel

from app.market.enums import SessionType


class TradingSession(BaseModel):
    """Trading session window for an exchange."""

    exchange: str
    session_type: SessionType
    session_name: str
    start_time: time
    end_time: time
    is_default: bool = False
