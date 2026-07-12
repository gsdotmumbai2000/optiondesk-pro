"""Build engine bundle from frozen engine providers."""

from app.events.event_bus import EventBus
from app.greeks.bootstrap import GreeksProvider
from app.margin.bootstrap import MarginProvider
from app.option_chain.bootstrap import OptionChainProvider
from app.payoff.bootstrap import PayoffProvider
from app.pricing.bootstrap import PricingProvider
from app.probability.bootstrap import ProbabilityProvider
from app.risk.bootstrap import RiskProvider
from app.strategy.engine.bundle import EngineBundle
from app.strategy.providers.engine_adapters import (
    GreeksServiceAdapter,
    MarginServiceAdapter,
    OptionChainServiceAdapter,
    PayoffServiceAdapter,
    PricingServiceAdapter,
    ProbabilityServiceAdapter,
    RiskServiceAdapter,
    VolatilityServiceAdapter,
)
from app.volatility.bootstrap import VolatilityProvider


def build_engine_bundle(event_bus: EventBus | None = None) -> EngineBundle:
    """Wire frozen engines into strategy engine bundle."""
    pricing = PricingProvider()
    greeks = GreeksProvider(event_bus)
    volatility = VolatilityProvider(event_bus)
    option_chain = OptionChainProvider(event_bus)
    probability = ProbabilityProvider(event_bus)
    payoff = PayoffProvider(event_bus)
    risk = RiskProvider(event_bus)
    margin = MarginProvider(event_bus)
    return EngineBundle(
        pricing=PricingServiceAdapter(pricing.service),
        greeks=GreeksServiceAdapter(greeks.service),
        volatility=VolatilityServiceAdapter(volatility.service),
        option_chain=OptionChainServiceAdapter(option_chain.service),
        probability=ProbabilityServiceAdapter(probability.service),
        payoff=PayoffServiceAdapter(payoff.service),
        risk=RiskServiceAdapter(risk.service),
        margin=MarginServiceAdapter(margin.service),
    )
