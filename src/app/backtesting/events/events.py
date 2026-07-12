"""Backtesting engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class ReplayStartedEvent(ApplicationEvent):
    """Published when replay begins."""


@dataclass(frozen=True, slots=True)
class ReplayPausedEvent(ApplicationEvent):
    """Published when replay is paused."""


@dataclass(frozen=True, slots=True)
class ReplayFinishedEvent(ApplicationEvent):
    """Published when replay completes."""


@dataclass(frozen=True, slots=True)
class TradeExecutedEvent(ApplicationEvent):
    """Published when a trade is executed."""


@dataclass(frozen=True, slots=True)
class BacktestCompletedEvent(ApplicationEvent):
    """Published when backtest completes."""


@dataclass(frozen=True, slots=True)
class PerformanceUpdatedEvent(ApplicationEvent):
    """Published when performance metrics update."""
