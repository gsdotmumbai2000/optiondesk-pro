"""Volatility analysis request."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot
from app.greeks.models.greeks_result import GreeksResult
from app.pricing.models.pricing_result import PricingResult
from app.volatility.models.snapshots import (
    HistoricalDataSnapshot,
    VolatilityMarketSnapshot,
)


@dataclass(frozen=True, slots=True)
class VolatilityAnalysisRequest:
    """Immutable input bundle for volatility analytics."""

    context: CalculationContext
    pricing_result: PricingResult
    greeks_result: GreeksResult
    market_snapshot: VolatilityMarketSnapshot
    historical_data: HistoricalDataSnapshot
    option_chain: OptionChainSnapshot
