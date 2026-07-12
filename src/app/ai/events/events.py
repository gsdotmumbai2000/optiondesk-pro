"""AI engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class RecommendationGeneratedEvent(ApplicationEvent):
    """Published when recommendations are generated."""


@dataclass(frozen=True, slots=True)
class RecommendationAcceptedEvent(ApplicationEvent):
    """Published when a recommendation is accepted."""


@dataclass(frozen=True, slots=True)
class RecommendationDismissedEvent(ApplicationEvent):
    """Published when a recommendation is dismissed."""


@dataclass(frozen=True, slots=True)
class RecommendationUpdatedEvent(ApplicationEvent):
    """Published when a recommendation is updated."""
