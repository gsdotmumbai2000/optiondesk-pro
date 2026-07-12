"""Probability analysis request."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.option_chain.models.analysis import OptionChainAnalysis
from app.pricing.models.pricing_result import PricingResult
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class ProbabilityAnalysisRequest:
    """Immutable input bundle for probability analytics."""

    context: CalculationContext
    pricing_result: PricingResult
    greeks_result: GreeksResult
    volatility_result: VolatilityResult
    chain_analysis: OptionChainAnalysis
