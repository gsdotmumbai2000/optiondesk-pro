"""Probability engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class ProbabilityCalculatedEvent(ApplicationEvent):
    """Published when probability analytics are calculated."""


@dataclass(frozen=True, slots=True)
class ProbabilityUpdatedEvent(ApplicationEvent):
    """Published when cached probability results update."""
