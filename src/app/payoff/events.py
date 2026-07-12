"""Payoff engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class PayoffCalculatedEvent(ApplicationEvent):
    """Published when payoff analytics are calculated."""


@dataclass(frozen=True, slots=True)
class PayoffUpdatedEvent(ApplicationEvent):
    """Published when cached payoff results update."""


@dataclass(frozen=True, slots=True)
class PayoffCurveUpdatedEvent(ApplicationEvent):
    """Published when payoff curve metrics update."""


@dataclass(frozen=True, slots=True)
class BreakevenUpdatedEvent(ApplicationEvent):
    """Published when breakeven prices update."""
