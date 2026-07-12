"""Margin engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class MarginCalculatedEvent(ApplicationEvent):
    """Published when margin analytics are calculated."""


@dataclass(frozen=True, slots=True)
class MarginUpdatedEvent(ApplicationEvent):
    """Published when cached margin results update."""


@dataclass(frozen=True, slots=True)
class BuyingPowerUpdatedEvent(ApplicationEvent):
    """Published when buying power metrics update."""


@dataclass(frozen=True, slots=True)
class MarginOptimizationCompletedEvent(ApplicationEvent):
    """Published when margin optimization completes."""
