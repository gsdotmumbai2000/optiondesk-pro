"""Orchestration package."""

__all__ = [
    "ApplicationCoordinator",
    "EngineRegistry",
    "WorkspaceCoordinator",
    "build_engine_registry",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "ApplicationCoordinator":
        from app.application.orchestration.application_coordinator import (
            ApplicationCoordinator,
        )

        return ApplicationCoordinator
    if name == "EngineRegistry":
        from app.application.registry.engine_registry import EngineRegistry

        return EngineRegistry
    if name == "WorkspaceCoordinator":
        from app.application.orchestration.workspace_coordinator import (
            WorkspaceCoordinator,
        )

        return WorkspaceCoordinator
    if name == "build_engine_registry":
        from app.application.registry.registry_factory import build_engine_registry

        return build_engine_registry
    raise AttributeError(name)
