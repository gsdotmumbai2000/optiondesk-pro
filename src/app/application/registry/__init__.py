"""Neutral engine registry package."""

__all__ = ["EngineRegistry", "build_engine_registry"]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "EngineRegistry":
        from app.application.registry.engine_registry import EngineRegistry

        return EngineRegistry
    if name == "build_engine_registry":
        from app.application.registry.registry_factory import build_engine_registry

        return build_engine_registry
    raise AttributeError(name)
