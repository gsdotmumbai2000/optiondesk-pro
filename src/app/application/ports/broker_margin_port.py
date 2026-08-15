"""Broker margin port for application workspaces."""

from typing import Protocol

from app.margin.models.broker_response import BrokerMarginResponse
from app.strategy.models.leg import StrategyLeg


class BrokerMarginPort(Protocol):
    """On-demand real-broker margin lookup for a strategy's legs."""

    def calculate_margin(
        self, legs: tuple[StrategyLeg, ...], exchange: str
    ) -> BrokerMarginResponse | None:
        """Return real broker margin for the legs, or None when unavailable
        (no broker connected, broker doesn't support it, or the call
        failed) -- callers fall back to the existing estimated margin."""
