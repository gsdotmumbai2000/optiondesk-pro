"""Expiry domain models."""

from datetime import date, datetime

from pydantic import BaseModel

from app.market.enums import ExpiryType, Weekday


class ExpiryRule(BaseModel):
    """Expiry convention for an underlying."""

    underlying: str
    expiry_type: ExpiryType
    weekday: Weekday | None = None
    rule: str = "LAST_WEEKDAY"
    expiry_time: str = "15:30:00"
    is_active: bool = True


class ExpiryRecord(BaseModel):
    """Resolved expiry date for an underlying."""

    underlying: str
    expiry_date: date
    expiry_type: ExpiryType
    expiry_datetime: datetime | None = None
    is_shifted: bool = False
    original_date: date | None = None
