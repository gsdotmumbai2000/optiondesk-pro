"""Broker integration events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class BrokerConnectedEvent(ApplicationEvent):
    """Published when a broker connection is established."""


@dataclass(frozen=True, slots=True)
class BrokerDisconnectedEvent(ApplicationEvent):
    """Published when a broker disconnects."""


@dataclass(frozen=True, slots=True)
class SessionExpiredEvent(ApplicationEvent):
    """Published when a broker session expires."""


@dataclass(frozen=True, slots=True)
class OrderPlacedEvent(ApplicationEvent):
    """Published when an order is placed."""


@dataclass(frozen=True, slots=True)
class OrderModifiedEvent(ApplicationEvent):
    """Published when an order is modified."""


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent(ApplicationEvent):
    """Published when an order is cancelled."""


@dataclass(frozen=True, slots=True)
class QuoteUpdatedEvent(ApplicationEvent):
    """Published when a live quote is received."""


@dataclass(frozen=True, slots=True)
class OptionChainUpdatedEvent(ApplicationEvent):
    """Published when option chain data is updated."""


@dataclass(frozen=True, slots=True)
class PortfolioUpdatedEvent(ApplicationEvent):
    """Published when portfolio data changes."""
