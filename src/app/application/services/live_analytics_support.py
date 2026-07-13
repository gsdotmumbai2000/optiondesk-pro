"""Shared live analytics helpers for workspace services."""

from app.application.ports.live_analytics_port import LiveAnalyticsPort
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
