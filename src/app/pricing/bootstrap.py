"""Pricing engine bootstrap."""

from app.pricing.black_scholes.engine import BlackScholesEngine
from app.pricing.services.pricing_service import PricingService
from app.pricing.validation.pricing_validator import PricingValidator


class PricingProvider:
    """Wire pricing engine dependencies."""

    def __init__(
        self,
        engine: BlackScholesEngine | None = None,
        validator: PricingValidator | None = None,
    ) -> None:
        """Initialize pricing provider."""
        self.engine = engine or BlackScholesEngine()
        self.validator = validator or PricingValidator()
        self.service = PricingService(self.engine, self.validator)
