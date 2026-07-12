"""Broker profile domain models."""

from pydantic import BaseModel, Field


class BrokerProfile(BaseModel):
    """Normalized broker user profile."""

    broker_code: str
    account_id: str = ""
    user_name: str = ""
    email: str = ""
    segments_allowed: dict[str, str] = Field(default_factory=dict)
    exchange_status: dict[str, str] = Field(default_factory=dict)
    raw_metadata: dict[str, str] = Field(default_factory=dict)
