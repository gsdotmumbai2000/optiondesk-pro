"""Simulator (NIFTY tick recording) domain events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class RecordingTickCapturedEvent(ApplicationEvent):
    """Published each time TickRecorder writes a NIFTY tick to disk."""
