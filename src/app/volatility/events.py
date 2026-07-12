"""Volatility engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class VolatilityCalculatedEvent(ApplicationEvent):
    """Published when volatility analytics are calculated."""


@dataclass(frozen=True, slots=True)
class VolatilityUpdatedEvent(ApplicationEvent):
    """Published when cached volatility results update."""
