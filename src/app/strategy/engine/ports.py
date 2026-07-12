"""Engine service ports for dependency injection."""

from typing import Protocol

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult
from app.option_chain.models.analysis import OptionChainAnalysis
from app.option_chain.models.request import OptionChainAnalysisRequest
from app.payoff.models.request import PayoffAnalysisRequest
from app.payoff.models.result import PayoffResult
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult
from app.probability.models.probability_result import ProbabilityResult
from app.probability.models.request import ProbabilityAnalysisRequest
from app.risk.models.request import RiskAnalysisRequest
from app.risk.models.result import RiskResult
from app.volatility.models.request import VolatilityAnalysisRequest
from app.volatility.models.volatility_result import VolatilityResult


class PricingEnginePort(Protocol):
    """Pricing engine port."""

    def price(
        self, context: CalculationContext, contract: OptionContract
    ) -> PricingResult: ...


class GreeksEnginePort(Protocol):
    """Greeks engine port."""

    def calculate_greeks(
        self,
        context: CalculationContext,
        contract: OptionContract,
        pricing_result: PricingResult,
    ) -> GreeksResult: ...


class VolatilityEnginePort(Protocol):
    """Volatility engine port."""

    def calculate(self, request: VolatilityAnalysisRequest) -> VolatilityResult: ...


class OptionChainEnginePort(Protocol):
    """Option chain analytics port."""

    def analyze(self, request: OptionChainAnalysisRequest) -> OptionChainAnalysis: ...


class ProbabilityEnginePort(Protocol):
    """Probability engine port."""

    def calculate(self, request: ProbabilityAnalysisRequest) -> ProbabilityResult: ...


class PayoffEnginePort(Protocol):
    """Payoff engine port."""

    def calculate(self, request: PayoffAnalysisRequest) -> PayoffResult: ...


class RiskEnginePort(Protocol):
    """Risk engine port."""

    def calculate(self, request: RiskAnalysisRequest) -> RiskResult: ...


class MarginEnginePort(Protocol):
    """Margin engine port."""

    def calculate(self, request: MarginAnalysisRequest) -> MarginResult: ...
