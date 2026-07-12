"""Strategy optimizer events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class OptimizationStartedEvent(ApplicationEvent):
    """Published when optimization begins."""


@dataclass(frozen=True, slots=True)
class OptimizationCompletedEvent(ApplicationEvent):
    """Published when optimization completes."""


@dataclass(frozen=True, slots=True)
class RecommendationGeneratedEvent(ApplicationEvent):
    """Published when recommendation is generated."""
