"""Holiday domain models."""

from datetime import date, time

from pydantic import BaseModel

from app.market.enums import SessionType


class Holiday(BaseModel):
    """Exchange trading holiday."""

    exchange: str
    holiday_date: date
    holiday_name: str
    holiday_type: str = "FULL"
    is_emergency: bool = False


class SpecialSession(BaseModel):
    """Special or muhurat trading session."""

    exchange: str
    session_date: date
    session_type: SessionType
    session_name: str
    start_time: time
    end_time: time
    is_half_day: bool = False
