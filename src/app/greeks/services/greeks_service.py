"""Greeks application service."""

from app.calculation.context.calculation_context import CalculationContext
from app.events.event_bus import EventBus
from app.greeks.cache.greeks_cache import GreeksCache
from app.greeks.engine.greeks_engine import GreeksEngine
from app.greeks.events import GreeksCalculatedEvent, GreeksUpdatedEvent
from app.greeks.exceptions import GreeksException
from app.greeks.models.greeks_result import GreeksResult
from app.greeks.providers.cache_keys import build_cache_key
from app.greeks.validation.greeks_validator import GreeksValidator
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult


class GreeksService:
    """Orchestrate Greeks analytics, caching, and events."""

    def __init__(
        self,
        engine: GreeksEngine,
        validator: GreeksValidator | None = None,
        cache: GreeksCache | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or GreeksValidator()
        self._cache = cache or GreeksCache()
        self._event_bus = event_bus

    @property
    def cache(self) -> GreeksCache:
        """Return Greeks cache."""
        return self._cache

    @property
    def engine(self) -> GreeksEngine:
        """Return Greeks engine."""
        return self._engine

    def calculate_greeks(
        self,
        context: CalculationContext,
        contract: OptionContract,
        pricing_result: PricingResult,
    ) -> GreeksResult:
        """Calculate and cache Greeks."""
        try:
            self._validator.validate(context, contract, pricing_result)
            result = self._engine.calculate_greeks(context, contract, pricing_result)
            key = build_cache_key(context, contract)
            self._cache.put(key, result)
            self._publish_events(key)
            return result
        except GreeksException:
            raise

    def get_latest(
        self,
        context: CalculationContext,
        contract: OptionContract,
    ) -> GreeksResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(context, contract))

    def refresh(
        self,
        context: CalculationContext,
        contract: OptionContract,
        pricing_result: PricingResult,
    ) -> GreeksResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(context, contract))
        return self.calculate_greeks(context, contract, pricing_result)

    def _publish_events(self, key: str) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(GreeksCalculatedEvent(payload=payload))
        self._event_bus.publish(GreeksUpdatedEvent(payload=payload))
