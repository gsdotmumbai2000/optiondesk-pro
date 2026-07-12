"""Margin provider port."""

from typing import Protocol

from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.request import MarginAnalysisRequest


class MarginProvider(Protocol):
    """Margin provider contract for broker adapters."""

    @property
    def provider_id(self) -> str:
        """Return provider identifier."""
        ...

    def supports_broker(self, broker_id: str) -> bool:
        """Return whether this provider supports the broker."""
        ...

    def calculate(self, request: MarginAnalysisRequest) -> BrokerMarginResponse:
        """Calculate or resolve margin for the request."""
        ...
