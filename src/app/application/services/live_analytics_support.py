"""Shared live analytics helpers for workspace services."""

from app.application.ports.live_analytics_port import LiveAnalyticsPort
from app.live.calculations.evaluation_context import EvaluationContext
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.option_chain import LiveOptionChain


class LiveAnalyticsSupport:
    """Mixin-style helper for workspace services."""

    def __init__(self, live_analytics: LiveAnalyticsPort | None = None) -> None:
        self._live_analytics = live_analytics

    def live_option_chain(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveOptionChain | None:
        if self._live_analytics is None:
            return None
        return self._live_analytics.get_chain(underlying, exchange, expiry_date)

    def live_analytics_snapshot(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveAnalyticsSnapshot | None:
        if self._live_analytics is None:
            return None
        return self._live_analytics.get_analytics(underlying, exchange, expiry_date)

    def refresh_live_analytics(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveAnalyticsSnapshot | None:
        """Synchronously recompute and return analytics for a chain key
        (unlike live_analytics_snapshot(), which only reads whatever the
        tick-driven pipeline last cached)."""
        if self._live_analytics is None:
            return None
        return self._live_analytics.refresh_and_get_analytics(underlying, exchange, expiry_date)

    def evaluation_context(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> EvaluationContext | None:
        """Build the raw context bundle (CalculationContext, reference
        contract, chain snapshot, and market/volatility/historical
        snapshots) needed to construct a StrategyEvaluationRequest or
        OptimizationRequest directly."""
        if self._live_analytics is None:
            return None
        return self._live_analytics.build_evaluation_context(underlying, exchange, expiry_date)
