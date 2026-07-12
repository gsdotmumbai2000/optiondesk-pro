"""Black-Scholes pricing package."""

__all__ = [
    "BlackScholesEngine",
    "OptionContract",
    "PricingProvider",
    "PricingResult",
    "PricingService",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "BlackScholesEngine":
        from app.pricing.black_scholes.engine import BlackScholesEngine

        return BlackScholesEngine
    if name == "OptionContract":
        from app.pricing.models.option_contract import OptionContract

        return OptionContract
    if name == "PricingProvider":
        from app.pricing.bootstrap import PricingProvider

        return PricingProvider
    if name == "PricingResult":
        from app.pricing.models.pricing_result import PricingResult

        return PricingResult
    if name == "PricingService":
        from app.pricing.services.pricing_service import PricingService

        return PricingService
    raise AttributeError(name)
