"""Greeks engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class GreeksCalculatedEvent(ApplicationEvent):
    """Published when Greeks analytics are calculated."""


@dataclass(frozen=True, slots=True)
class GreeksUpdatedEvent(ApplicationEvent):
    """Published when cached Greeks results update."""
