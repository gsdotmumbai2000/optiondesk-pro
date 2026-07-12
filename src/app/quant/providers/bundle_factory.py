"""Quant engine bundle factory."""

from app.events.event_bus import EventBus
from app.quant.models.bundle import QuantEngineProviders
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


def build_strategy_engine_bundle(
    providers: QuantEngineProviders,
) -> EngineBundle:
    """Wire quantitative providers into strategy engine bundle."""
    return EngineBundle(
        pricing=PricingServiceAdapter(providers.pricing.service),
        greeks=GreeksServiceAdapter(providers.greeks.service),
        volatility=VolatilityServiceAdapter(providers.volatility.service),
        option_chain=OptionChainServiceAdapter(providers.option_chain.service),
        probability=ProbabilityServiceAdapter(providers.probability.service),
        payoff=PayoffServiceAdapter(providers.payoff.service),
        risk=RiskServiceAdapter(providers.risk.service),
        margin=MarginServiceAdapter(providers.margin.service),
    )


def build_quant_engine_bundle(event_bus: EventBus | None = None) -> EngineBundle:
    """Build strategy engine bundle from default quantitative providers."""
    from app.quant.bootstrap import QuantProvider

    return QuantProvider(event_bus).build_engine_bundle()
