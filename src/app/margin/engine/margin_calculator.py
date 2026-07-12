"""Margin calculator."""

from datetime import datetime, timezone
from decimal import Decimal

from app.margin.adapters.broker_margin_provider import BrokerMarginProvider
from app.margin.adapters.estimated_margin_provider import EstimatedMarginProvider
from app.margin.analytics.buying_power import buying_power, margin_utilization
from app.margin.analytics.capital_efficiency import capital_efficiency, leverage_ratio
from app.margin.analytics.portfolio_margin import portfolio_margin_totals, total_notional
from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.enums import MarginModelVersion, MarginSource
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult


class MarginCalculator:
    """Calculate full margin analytics from request bundle."""

    def __init__(
        self,
        estimated_provider: EstimatedMarginProvider | None = None,
        broker_provider: BrokerMarginProvider | None = None,
    ) -> None:
        """Initialize calculator."""
        self._estimated = estimated_provider or EstimatedMarginProvider()
        fallback = self._estimated
        self._broker = broker_provider or BrokerMarginProvider(fallback=fallback)

    def calculate(self, request: MarginAnalysisRequest) -> MarginResult:
        """Compute MarginResult from request."""
        legs = request.resolved_legs
        ctx = request.context
        source, response = self._resolve_margin(request)
        totals = portfolio_margin_totals(legs, ctx, request.risk_result)
        notional = total_notional(legs, ctx)
        cap_required = response.total_margin
        util = margin_utilization(response)
        bp = buying_power(response)
        cap_eff = capital_efficiency(request.payoff_result, cap_required)
        lev = leverage_ratio(notional, cap_required)
        peak = max(response.total_margin, totals["total"])
        reduction = totals["benefit"]

        return MarginResult(
            initial_margin=response.initial_margin,
            exposure_margin=response.exposure_margin,
            span_margin=response.span_margin,
            portfolio_margin=totals["portfolio"],
            additional_margin=totals["additional"],
            peak_margin=peak,
            total_margin=response.total_margin,
            available_margin=response.available_margin,
            margin_utilization=util,
            buying_power=bp,
            capital_required=cap_required,
            capital_efficiency=cap_eff,
            leverage_ratio=lev,
            margin_benefit=totals["benefit"],
            margin_reduction=reduction,
            margin_source=source,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=MarginModelVersion.V1,
        )

    def _resolve_margin(
        self,
        request: MarginAnalysisRequest,
    ) -> tuple[MarginSource, BrokerMarginResponse]:
        if request.broker_response is not None:
            return MarginSource.BROKER, request.broker_response
        estimated = self._estimated.calculate(request)
        return MarginSource.ESTIMATED, estimated
