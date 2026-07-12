"""Strategy engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class StrategyCreatedEvent(ApplicationEvent):
    """Published when a strategy is created."""


@dataclass(frozen=True, slots=True)
class StrategyModifiedEvent(ApplicationEvent):
    """Published when a strategy is modified."""


@dataclass(frozen=True, slots=True)
class StrategyEvaluatedEvent(ApplicationEvent):
    """Published when a strategy is evaluated."""


@dataclass(frozen=True, slots=True)
class StrategyDeletedEvent(ApplicationEvent):
    """Published when a strategy is deleted."""


@dataclass(frozen=True, slots=True)
class StrategyComparedEvent(ApplicationEvent):
    """Published when strategies are compared."""
