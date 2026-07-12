"""Expected value analytics."""

from decimal import Decimal

from app.option_chain.models.analysis import OptionChainAnalysis
from app.pricing.models.pricing_result import PricingResult
from app.volatility.models.volatility_result import VolatilityResult


def expected_value(
    pricing_result: PricingResult,
    volatility: VolatilityResult,
    chain_analysis: OptionChainAnalysis,
) -> Decimal:
    """Estimate expected value from pricing and chain liquidity."""
    base = pricing_result.theoretical_price
    liquidity_factor = chain_analysis.liquidity_score / Decimal("100")
    vol_adjustment = volatility.expected_move.to_expiry * liquidity_factor * Decimal("0.1")
    return base + vol_adjustment
