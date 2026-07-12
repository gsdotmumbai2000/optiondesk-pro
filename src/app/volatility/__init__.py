"""Enterprise Volatility Engine."""

__all__ = [
    "VolatilityAnalysisRequest",
    "VolatilityEngine",
    "VolatilityProvider",
    "VolatilityResult",
    "VolatilityService",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "VolatilityAnalysisRequest":
        from app.volatility.models.request import VolatilityAnalysisRequest

        return VolatilityAnalysisRequest
    if name == "VolatilityEngine":
        from app.volatility.engine.volatility_engine import VolatilityEngine

        return VolatilityEngine
    if name == "VolatilityProvider":
        from app.volatility.bootstrap import VolatilityProvider

        return VolatilityProvider
    if name == "VolatilityResult":
        from app.volatility.models.volatility_result import VolatilityResult

        return VolatilityResult
    if name == "VolatilityService":
        from app.volatility.services.volatility_service import VolatilityService

        return VolatilityService
    raise AttributeError(name)
