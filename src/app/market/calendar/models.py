"""Market calendar models."""

from pydantic import BaseModel, Field


class MarketCalendarConfig(BaseModel):
    """Per-exchange calendar configuration."""

    exchange: str
    timezone: str = "Asia/Kolkata"
    weekend_days: list[str] = Field(default_factory=lambda: ["SATURDAY", "SUNDAY"])
    supports_muhurat: bool = True
    supports_half_days: bool = True
