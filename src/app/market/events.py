"""Market Master events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class InstrumentLoadedEvent(ApplicationEvent):
    """Published when instrument master data is loaded."""


@dataclass(frozen=True, slots=True)
class CalendarLoadedEvent(ApplicationEvent):
    """Published when market calendar data is loaded."""


@dataclass(frozen=True, slots=True)
class ExpiryLoadedEvent(ApplicationEvent):
    """Published when expiry calendar is loaded."""


@dataclass(frozen=True, slots=True)
class HolidayLoadedEvent(ApplicationEvent):
    """Published when holiday calendar is loaded."""
