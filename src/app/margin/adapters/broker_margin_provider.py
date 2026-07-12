"""Broker margin provider."""

from app.margin.adapters.port import MarginProvider
from app.margin.exceptions import InvalidMarginInput
from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.request import MarginAnalysisRequest


class BrokerMarginProvider:
    """Use normalized broker margin response from request."""

    def __init__(self, *, fallback: MarginProvider | None = None) -> None:
        """Initialize with optional fallback provider."""
        self._fallback = fallback

    @property
    def provider_id(self) -> str:
        """Return provider identifier."""
        return "broker"

    def supports_broker(self, broker_id: str) -> bool:
        """Broker provider supports when response is present."""
        return bool(broker_id)

    def calculate(self, request: MarginAnalysisRequest) -> BrokerMarginResponse:
        """Return broker response or fall back to estimation."""
        if request.broker_response is not None:
            return request.broker_response
        if self._fallback is not None:
            return self._fallback.calculate(request)
        raise InvalidMarginInput("broker_response required for BrokerMarginProvider")
