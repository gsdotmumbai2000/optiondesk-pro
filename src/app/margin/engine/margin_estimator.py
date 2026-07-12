"""Margin estimator."""

from app.margin.adapters.estimated_margin_provider import EstimatedMarginProvider
from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.request import MarginAnalysisRequest


class MarginEstimator:
    """Estimate margin without broker response."""

    def __init__(
        self,
        provider: EstimatedMarginProvider | None = None,
    ) -> None:
        """Initialize estimator."""
        self._provider = provider or EstimatedMarginProvider()

    def estimate(self, request: MarginAnalysisRequest) -> BrokerMarginResponse:
        """Return estimated broker margin response."""
        return self._provider.calculate(request)
