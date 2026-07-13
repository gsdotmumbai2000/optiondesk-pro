"""Enterprise market data events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class PriceUpdatedEvent(ApplicationEvent):
    """Published when last traded price changes."""


@dataclass(frozen=True, slots=True)
class QuoteUpdatedEvent(ApplicationEvent):
    """Published when a normalized quote is updated."""


@dataclass(frozen=True, slots=True)
class OptionUpdatedEvent(ApplicationEvent):
    """Published when an option quote is updated."""


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
    """Published when a subscription is added."""


@dataclass(frozen=True, slots=True)
class SubscriptionRemovedEvent(ApplicationEvent):
    """Published when a subscription is removed."""


@dataclass(frozen=True, slots=True)
class ConnectionEstablishedEvent(ApplicationEvent):
    """Published when live feed connection is established."""


@dataclass(frozen=True, slots=True)
class ConnectionLostEvent(ApplicationEvent):
    """Published when live feed connection is lost."""


@dataclass(frozen=True, slots=True)
class ReconnectStartedEvent(ApplicationEvent):
    """Published when feed reconnect begins."""


@dataclass(frozen=True, slots=True)
class ReconnectCompletedEvent(ApplicationEvent):
    """Published when feed reconnect completes."""
