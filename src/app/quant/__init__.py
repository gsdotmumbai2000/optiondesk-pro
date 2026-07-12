"""Quantitative Engine Integration Layer."""

__all__ = [
    "QuantEngineProviders",
    "QuantEngineRegistry",
    "QuantProvider",
    "QuantService",
    "build_quant_engine_bundle",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "QuantEngineProviders":
        from app.quant.models.bundle import QuantEngineProviders

        return QuantEngineProviders
    if name == "QuantEngineRegistry":
        from app.quant.registry.engine_registry import QuantEngineRegistry

        return QuantEngineRegistry
    if name == "QuantProvider":
        from app.quant.bootstrap import QuantProvider

        return QuantProvider
    if name == "QuantService":
        from app.quant.services.quant_service import QuantService

        return QuantService
    if name == "build_quant_engine_bundle":
        from app.quant.providers.bundle_factory import build_quant_engine_bundle

        return build_quant_engine_bundle
    raise AttributeError(name)
