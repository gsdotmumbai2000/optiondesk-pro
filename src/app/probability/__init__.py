"""Enterprise Probability Engine."""

__all__ = [
    "ProbabilityAnalysisRequest",
    "ProbabilityProvider",
    "ProbabilityResult",
    "ProbabilityService",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "ProbabilityAnalysisRequest":
        from app.probability.models.request import ProbabilityAnalysisRequest

        return ProbabilityAnalysisRequest
    if name == "ProbabilityProvider":
        from app.probability.bootstrap import ProbabilityProvider

        return ProbabilityProvider
    if name == "ProbabilityResult":
        from app.probability.models.probability_result import ProbabilityResult

        return ProbabilityResult
    if name == "ProbabilityService":
        from app.probability.services.probability_service import ProbabilityService

        return ProbabilityService
    raise AttributeError(name)
