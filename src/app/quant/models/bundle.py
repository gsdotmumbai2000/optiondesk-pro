"""Quantitative engine provider bundle."""

from dataclasses import dataclass

from app.greeks.bootstrap import GreeksProvider
from app.margin.bootstrap import MarginProvider
from app.option_chain.bootstrap import OptionChainProvider
from app.payoff.bootstrap import PayoffProvider
from app.pricing.bootstrap import PricingProvider
from app.probability.bootstrap import ProbabilityProvider
from app.risk.bootstrap import RiskProvider
from app.volatility.bootstrap import VolatilityProvider


@dataclass(frozen=True, slots=True)
class QuantEngineProviders:
    """Immutable bundle of quantitative engine providers."""

    pricing: PricingProvider
    greeks: GreeksProvider
    volatility: VolatilityProvider
    option_chain: OptionChainProvider
    probability: ProbabilityProvider
    payoff: PayoffProvider
    risk: RiskProvider
    margin: MarginProvider
