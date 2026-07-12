"""Option chain engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class OptionChainAnalyzedEvent(ApplicationEvent):
    """Published when option chain analytics are calculated."""


@dataclass(frozen=True, slots=True)
class OptionChainUpdatedEvent(ApplicationEvent):
    """Published when cached option chain results update."""
