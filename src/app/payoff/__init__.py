"""Enterprise Payoff Engine."""

__all__ = [
    "PayoffAnalysisRequest",
    "PayoffEngine",
    "PayoffProvider",
    "PayoffResult",
    "PayoffService",
    "PortfolioPosition",
    "StrategyLeg",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "PayoffAnalysisRequest":
        from app.payoff.models.request import PayoffAnalysisRequest

        return PayoffAnalysisRequest
    if name == "PayoffEngine":
        from app.payoff.engine.payoff_engine import PayoffEngine

        return PayoffEngine
    if name == "PayoffProvider":
        from app.payoff.bootstrap import PayoffProvider

        return PayoffProvider
    if name == "PayoffResult":
        from app.payoff.models.result import PayoffResult

        return PayoffResult
    if name == "PayoffService":
        from app.payoff.services.payoff_service import PayoffService

        return PayoffService
    if name == "PortfolioPosition":
        from app.payoff.models.legs import PortfolioPosition

        return PortfolioPosition
    if name == "StrategyLeg":
        from app.payoff.models.legs import StrategyLeg

        return StrategyLeg
    raise AttributeError(name)
