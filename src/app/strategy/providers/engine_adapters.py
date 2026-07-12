"""Adapters wrapping frozen engine services."""

from app.greeks.services.greeks_service import GreeksService
from app.margin.services.margin_service import MarginService
from app.option_chain.services.analytics_service import OptionChainAnalyticsService
from app.payoff.services.payoff_service import PayoffService
from app.pricing.services.pricing_service import PricingService
from app.probability.services.probability_service import ProbabilityService
from app.risk.services.risk_service import RiskService
from app.volatility.services.volatility_service import VolatilityService


class PricingServiceAdapter:
    """Adapter for PricingService."""

    def __init__(self, service: PricingService) -> None:
        self._service = service

    def price(self, context, contract):
        return self._service.price(context, contract)


class GreeksServiceAdapter:
    """Adapter for GreeksService."""

    def __init__(self, service: GreeksService) -> None:
        self._service = service

    def calculate_greeks(self, context, contract, pricing_result):
        return self._service.calculate_greeks(context, contract, pricing_result)


class VolatilityServiceAdapter:
    """Adapter for VolatilityService."""

    def __init__(self, service: VolatilityService) -> None:
        self._service = service

    def calculate(self, request):
        return self._service.calculate(request)


class OptionChainServiceAdapter:
    """Adapter for OptionChainAnalyticsService."""

    def __init__(self, service: OptionChainAnalyticsService) -> None:
        self._service = service

    def analyze(self, request):
        return self._service.analyze(request)


class ProbabilityServiceAdapter:
    """Adapter for ProbabilityService."""

    def __init__(self, service: ProbabilityService) -> None:
        self._service = service

    def calculate(self, request):
        return self._service.calculate(request)


class PayoffServiceAdapter:
    """Adapter for PayoffService."""

    def __init__(self, service: PayoffService) -> None:
        self._service = service

    def calculate(self, request):
        return self._service.calculate(request)


class RiskServiceAdapter:
    """Adapter for RiskService."""

    def __init__(self, service: RiskService) -> None:
        self._service = service

    def calculate(self, request):
        return self._service.calculate(request)


class MarginServiceAdapter:
    """Adapter for MarginService."""

    def __init__(self, service: MarginService) -> None:
        self._service = service

    def calculate(self, request):
        return self._service.calculate(request)
