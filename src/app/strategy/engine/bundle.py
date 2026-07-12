"""Engine bundle for dependency injection."""

from dataclasses import dataclass

from app.strategy.engine.ports import (
    GreeksEnginePort,
    MarginEnginePort,
    OptionChainEnginePort,
    PayoffEnginePort,
    PricingEnginePort,
    ProbabilityEnginePort,
    RiskEnginePort,
    VolatilityEnginePort,
)


@dataclass(frozen=True, slots=True)
class EngineBundle:
    """Immutable bundle of engine service ports."""

    pricing: PricingEnginePort
    greeks: GreeksEnginePort
    volatility: VolatilityEnginePort
    option_chain: OptionChainEnginePort
    probability: ProbabilityEnginePort
    payoff: PayoffEnginePort
    risk: RiskEnginePort
    margin: MarginEnginePort
