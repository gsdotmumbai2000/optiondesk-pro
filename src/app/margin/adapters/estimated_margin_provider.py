"""Estimated margin provider."""

from datetime import datetime, timezone
from decimal import Decimal

from app.margin.adapters.port import MarginProvider
from app.margin.analytics.portfolio_margin import portfolio_margin_totals
from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.request import MarginAnalysisRequest


class EstimatedMarginProvider:
    """Estimate margin from positions without broker API."""

    @property
    def provider_id(self) -> str:
        """Return provider identifier."""
        return "estimated"

    def supports_broker(self, broker_id: str) -> bool:
        """Estimated provider supports all brokers."""
        return True

    def calculate(self, request: MarginAnalysisRequest) -> BrokerMarginResponse:
        """Estimate margin from legs and context."""
        legs = request.resolved_legs
        ctx = request.context
        totals = portfolio_margin_totals(legs, ctx, request.risk_result)
        account = ctx.spot_price * Decimal(ctx.lot_size) * Decimal("10")
        available = max(account - totals["total"], Decimal("0"))
        return BrokerMarginResponse(
            broker_id="estimated",
            initial_margin=totals["initial"],
            exposure_margin=totals["exposure"],
            span_margin=totals["span"],
            total_margin=totals["total"],
            available_margin=available,
            account_balance=account,
            captured_at=datetime.now(timezone.utc),
        )
