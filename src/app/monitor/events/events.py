"""Monitor engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class MonitoringStartedEvent(ApplicationEvent):
    """Published when monitoring session starts."""


@dataclass(frozen=True, slots=True)
class MonitoringStoppedEvent(ApplicationEvent):
    """Published when monitoring session stops."""


@dataclass(frozen=True, slots=True)
class AlertRaisedEvent(ApplicationEvent):
    """Published when an alert is raised."""


@dataclass(frozen=True, slots=True)
class AlertAcknowledgedEvent(ApplicationEvent):
    """Published when an alert is acknowledged."""


@dataclass(frozen=True, slots=True)
class RecommendationGeneratedEvent(ApplicationEvent):
    """Published when recommendations are generated."""
