"""Shared broker margin helper for workspace services."""

from app.application.ports.broker_margin_port import BrokerMarginPort
from app.margin.models.broker_response import BrokerMarginResponse
from app.strategy.models.leg import StrategyLeg


class BrokerMarginSupport:
    """Mixin-style helper for workspace services."""

    def __init__(self, broker_margin: BrokerMarginPort | None = None) -> None:
        self._broker_margin = broker_margin

    def broker_margin(
        self, legs: tuple[StrategyLeg, ...], exchange: str = "NFO"
    ) -> BrokerMarginResponse | None:
        """Return real broker margin for the legs, or None when no broker
        margin source is configured or the lookup is unavailable."""
        if self._broker_margin is None:
            return None
        return self._broker_margin.calculate_margin(legs, exchange)
