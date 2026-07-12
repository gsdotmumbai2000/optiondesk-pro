"""Market data engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class QuoteUpdatedEvent(ApplicationEvent):
    """Published when a normalized quote is updated."""


@dataclass(frozen=True, slots=True)
class FutureUpdatedEvent(ApplicationEvent):
    """Published when a futures quote is updated."""


@dataclass(frozen=True, slots=True)
class OptionChainUpdatedEvent(ApplicationEvent):
    """Published when option chain data is updated."""


@dataclass(frozen=True, slots=True)
class MarketOpenedEvent(ApplicationEvent):
    """Published when a market opens."""


@dataclass(frozen=True, slots=True)
class MarketClosedEvent(ApplicationEvent):
    """Published when a market closes."""


@dataclass(frozen=True, slots=True)
class SnapshotUpdatedEvent(ApplicationEvent):
    """Published when a market snapshot is captured."""


@dataclass(frozen=True, slots=True)
class TickReceivedEvent(ApplicationEvent):
    """Published when a live tick is received."""


@dataclass(frozen=True, slots=True)
class SubscriptionAddedEvent(ApplicationEvent):
    """Published when a live subscription is added."""


@dataclass(frozen=True, slots=True)
class SubscriptionRemovedEvent(ApplicationEvent):
    """Published when a live subscription is removed."""
