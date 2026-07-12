"""Quant engine events."""

from dataclasses import dataclass

from app.events.application_events import ApplicationEvent


@dataclass(frozen=True, slots=True)
class QuantEnginesInitializedEvent(ApplicationEvent):
    """Published when quantitative engines are initialized."""


@dataclass(frozen=True, slots=True)
class QuantBundleBuiltEvent(ApplicationEvent):
    """Published when a strategy engine bundle is built."""
