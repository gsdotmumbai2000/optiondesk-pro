"""Normalized broker margin response."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class BrokerMarginResponse:
    """Normalized broker margin response (adapter output)."""

    broker_id: str
    initial_margin: Decimal
    exposure_margin: Decimal
    span_margin: Decimal
    total_margin: Decimal
    available_margin: Decimal
    account_balance: Decimal
    captured_at: datetime
