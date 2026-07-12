"""Risk engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class RiskCalculatedEvent(ApplicationEvent):
    """Published when risk analytics are calculated."""


@dataclass(frozen=True, slots=True)
class StressCompletedEvent(ApplicationEvent):
    """Published when stress testing completes."""


@dataclass(frozen=True, slots=True)
class VaRUpdatedEvent(ApplicationEvent):
    """Published when VaR metrics update."""


@dataclass(frozen=True, slots=True)
class RiskLimitExceededEvent(ApplicationEvent):
    """Published when a risk limit is exceeded."""


@dataclass(frozen=True, slots=True)
class PortfolioUpdatedEvent(ApplicationEvent):
    """Published when portfolio risk metrics update."""
