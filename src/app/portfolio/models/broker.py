"""Broker position update model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.portfolio.models.enums import AssetClass


@dataclass(frozen=True, slots=True)
class BrokerPositionUpdate:
    """Normalized broker position update."""

    broker_id: str
    symbol: str
    asset_class: AssetClass
    quantity: int
    average_price: Decimal
    updated_at: datetime
