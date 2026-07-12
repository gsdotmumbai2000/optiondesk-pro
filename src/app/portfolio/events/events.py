"""Portfolio engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class PortfolioCreatedEvent(ApplicationEvent):
    """Published when a portfolio is created."""


@dataclass(frozen=True, slots=True)
class PortfolioUpdatedEvent(ApplicationEvent):
    """Published when portfolio state updates."""


@dataclass(frozen=True, slots=True)
class TradeRecordedEvent(ApplicationEvent):
    """Published when a trade is recorded."""


@dataclass(frozen=True, slots=True)
class PositionOpenedEvent(ApplicationEvent):
    """Published when a position is opened."""


@dataclass(frozen=True, slots=True)
class PositionClosedEvent(ApplicationEvent):
    """Published when a position is closed."""


@dataclass(frozen=True, slots=True)
class PerformanceUpdatedEvent(ApplicationEvent):
    """Published when performance metrics update."""
