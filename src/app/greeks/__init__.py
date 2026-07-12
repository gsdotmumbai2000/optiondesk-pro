"""Enterprise Greeks Engine."""

__all__ = [
    "GreeksEngine",
    "GreeksProvider",
    "GreeksResult",
    "GreeksService",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "GreeksEngine":
        from app.greeks.engine.greeks_engine import GreeksEngine

        return GreeksEngine
    if name == "GreeksProvider":
        from app.greeks.bootstrap import GreeksProvider

        return GreeksProvider
    if name == "GreeksResult":
        from app.greeks.models.greeks_result import GreeksResult

        return GreeksResult
    if name == "GreeksService":
        from app.greeks.services.greeks_service import GreeksService

        return GreeksService
    raise AttributeError(name)
