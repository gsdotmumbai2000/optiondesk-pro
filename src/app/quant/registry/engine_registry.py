"""Quantitative engine registry."""

from app.events.event_bus import EventBus
from app.greeks.bootstrap import GreeksProvider
from app.margin.bootstrap import MarginProvider
from app.option_chain.bootstrap import OptionChainProvider
from app.payoff.bootstrap import PayoffProvider
from app.pricing.bootstrap import PricingProvider
from app.probability.bootstrap import ProbabilityProvider
from app.quant.models.bundle import QuantEngineProviders
from app.risk.bootstrap import RiskProvider
from app.volatility.bootstrap import VolatilityProvider


class QuantEngineRegistry:
    """Register and expose quantitative engine providers."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize registry."""
        self._event_bus = event_bus
        self._providers = QuantEngineProviders(
            pricing=PricingProvider(),
            greeks=GreeksProvider(event_bus),
            volatility=VolatilityProvider(event_bus),
            option_chain=OptionChainProvider(event_bus),
            probability=ProbabilityProvider(event_bus),
            payoff=PayoffProvider(event_bus),
            risk=RiskProvider(event_bus),
            margin=MarginProvider(event_bus),
        )

    @property
    def providers(self) -> QuantEngineProviders:
        """Return quantitative engine providers."""
        return self._providers
