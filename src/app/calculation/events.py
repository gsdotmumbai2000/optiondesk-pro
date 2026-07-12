"""Calculation engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class CalculationContextCreatedEvent(ApplicationEvent):
    """Published when a calculation context is created."""


@dataclass(frozen=True, slots=True)
class CalculationContextUpdatedEvent(ApplicationEvent):
    """Published when a calculation context is updated."""


@dataclass(frozen=True, slots=True)
class CalculationContextInvalidEvent(ApplicationEvent):
    """Published when context validation fails."""
