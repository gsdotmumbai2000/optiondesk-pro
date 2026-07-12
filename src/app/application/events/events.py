"""Application layer UI events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class WorkspaceOpenedEvent(ApplicationEvent):
    """Published when a workspace is opened."""


@dataclass(frozen=True, slots=True)
class WorkspaceClosedEvent(ApplicationEvent):
    """Published when a workspace is closed."""


@dataclass(frozen=True, slots=True)
class StrategyLoadedEvent(ApplicationEvent):
    """Published when a strategy is loaded."""


@dataclass(frozen=True, slots=True)
class PortfolioLoadedEvent(ApplicationEvent):
    """Published when a portfolio is loaded."""


@dataclass(frozen=True, slots=True)
class BacktestStartedEvent(ApplicationEvent):
    """Published when a backtest is started."""


@dataclass(frozen=True, slots=True)
class RecommendationReadyEvent(ApplicationEvent):
    """Published when AI recommendations are ready."""
