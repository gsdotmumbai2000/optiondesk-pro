"""Tests for the quant module: purely orchestration/wiring (no formulas of
its own), so what's tested here is that it assembles the *right* real
provider services into the *right* engine adapters, and publishes the
expected lifecycle events -- not any calculation.
"""

from app.events.event_bus import EventBus
from app.quant.events import QuantBundleBuiltEvent, QuantEnginesInitializedEvent
from app.quant.providers.bundle_factory import build_strategy_engine_bundle
from app.quant.registry.engine_registry import QuantEngineRegistry
from app.quant.services.quant_service import QuantService
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


class TestQuantEngineRegistryBuildsAllRealProviders:
    def test_registry_exposes_all_eight_providers(self) -> None:
        registry = QuantEngineRegistry()

        providers = registry.providers

        assert providers.pricing is not None
        assert providers.greeks is not None
        assert providers.volatility is not None
        assert providers.option_chain is not None
        assert providers.probability is not None
        assert providers.payoff is not None
        assert providers.risk is not None
        assert providers.margin is not None

    def test_works_without_an_event_bus(self) -> None:
        registry = QuantEngineRegistry(event_bus=None)

        assert registry.providers.pricing is not None


class TestBuildStrategyEngineBundleWrapsCorrectAdapters:
    def test_each_bundle_field_wraps_the_matching_provider_in_the_right_adapter(self) -> None:
        registry = QuantEngineRegistry()

        bundle = build_strategy_engine_bundle(registry.providers)

        assert isinstance(bundle.pricing, PricingServiceAdapter)
        assert isinstance(bundle.greeks, GreeksServiceAdapter)
        assert isinstance(bundle.volatility, VolatilityServiceAdapter)
        assert isinstance(bundle.option_chain, OptionChainServiceAdapter)
        assert isinstance(bundle.probability, ProbabilityServiceAdapter)
        assert isinstance(bundle.payoff, PayoffServiceAdapter)
        assert isinstance(bundle.risk, RiskServiceAdapter)
        assert isinstance(bundle.margin, MarginServiceAdapter)


class TestQuantServiceLifecycleEvents:
    def test_publishes_initialized_event_on_construction(self) -> None:
        event_bus = EventBus()
        received: list = []
        event_bus.subscribe(QuantEnginesInitializedEvent, received.append)
        registry = QuantEngineRegistry(event_bus)

        QuantService(registry, event_bus)

        assert len(received) == 1

    def test_publishes_bundle_built_event_on_build_engine_bundle(self) -> None:
        event_bus = EventBus()
        received: list = []
        registry = QuantEngineRegistry(event_bus)
        service = QuantService(registry, event_bus)
        event_bus.subscribe(QuantBundleBuiltEvent, received.append)

        service.build_engine_bundle()

        assert len(received) == 1

    def test_works_without_an_event_bus_no_crash(self) -> None:
        registry = QuantEngineRegistry()
        service = QuantService(registry, event_bus=None)

        bundle = service.build_engine_bundle()

        assert isinstance(bundle.pricing, PricingServiceAdapter)

    def test_build_engine_bundle_delegates_to_bundle_factory(self) -> None:
        registry = QuantEngineRegistry()
        service = QuantService(registry, event_bus=None)

        bundle = service.build_engine_bundle()

        assert isinstance(bundle.greeks, GreeksServiceAdapter)
        assert isinstance(bundle.margin, MarginServiceAdapter)
