"""Live analytics events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent
from app.greeks.events import GreeksUpdatedEvent
from app.margin.events import MarginUpdatedEvent
from app.option_chain.events import OptionChainUpdatedEvent
from app.portfolio.events.events import PortfolioUpdatedEvent
from app.probability.events import ProbabilityUpdatedEvent
from app.risk.events import RiskCalculatedEvent
from app.volatility.events import VolatilityUpdatedEvent


@dataclass(frozen=True, slots=True)
class LiveOptionChainUpdatedEvent(ApplicationEvent):
    """Published when live option chain cache updates."""


@dataclass(frozen=True, slots=True)
class LiveAnalyticsRefreshedEvent(ApplicationEvent):
    """Published when a full analytics cycle completes."""


@dataclass(frozen=True, slots=True)
class PositionUpdatedEvent(ApplicationEvent):
    """Published when live position analytics update."""


__all__ = [
    "GreeksUpdatedEvent",
    "LiveAnalyticsRefreshedEvent",
    "LiveOptionChainUpdatedEvent",
    "MarginUpdatedEvent",
    "OptionChainUpdatedEvent",
    "PortfolioUpdatedEvent",
    "PositionUpdatedEvent",
    "ProbabilityUpdatedEvent",
    "RiskCalculatedEvent",
    "VolatilityUpdatedEvent",
]
