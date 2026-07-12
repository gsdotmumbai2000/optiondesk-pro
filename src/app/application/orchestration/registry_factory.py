"""Backward-compatible registry factory re-export."""

from app.application.registry.registry_factory import build_engine_registry

__all__ = ["build_engine_registry"]
