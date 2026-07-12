"""Calculation context service."""

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.events import CalculationContextUpdatedEvent
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.models.configuration import CalculationConfiguration
from app.calculation.services.context_cache import ContextCache
from app.calculation.services.context_serializer import ContextSerializer
from app.events.event_bus import EventBus


class CalculationContextService:
    """Orchestrate context creation, caching, and serialization."""

    def __init__(
        self,
        factory: CalculationContextFactory,
        cache: ContextCache | None = None,
        serializer: ContextSerializer | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._factory = factory
        self._cache = cache or ContextCache()
        self._serializer = serializer or ContextSerializer()
        self._event_bus = event_bus

    @property
    def cache(self) -> ContextCache:
        """Return context cache."""
        return self._cache

    @property
    def serializer(self) -> ContextSerializer:
        """Return context serializer."""
        return self._serializer

    def create_context(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
        *,
        configuration: CalculationConfiguration | None = None,
    ) -> CalculationContext:
        """Create and cache a calculation context."""
        context = self._factory.build(
            underlying,
            exchange,
            expiry,
            configuration=configuration,
        )
        key = self._cache_key(underlying, exchange, expiry)
        self._cache.put(key, context)
        self._publish_update(key)
        return context

    def get_latest(self, underlying: str, exchange: str, expiry: str) -> CalculationContext | None:
        """Return latest cached context."""
        return self._cache.get_latest(self._cache_key(underlying, exchange, expiry))

    def get_previous(self, underlying: str, exchange: str, expiry: str) -> CalculationContext | None:
        """Return previous cached context."""
        return self._cache.get_previous(self._cache_key(underlying, exchange, expiry))

    def compare_contexts(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
    ) -> dict[str, object] | None:
        """Compare latest and previous cached contexts."""
        return self._cache.compare(self._cache_key(underlying, exchange, expiry))

    def expire_context(self, underlying: str, exchange: str, expiry: str) -> None:
        """Expire a cached context."""
        self._cache.expire(self._cache_key(underlying, exchange, expiry))

    def export_context(self, context: CalculationContext) -> dict[str, object]:
        """Export context to dictionary."""
        return self._serializer.export(context)

    def import_context(self, data: dict[str, object]) -> CalculationContext:
        """Import context from dictionary."""
        return self._serializer.import_context(data)

    def export_json(self, context: CalculationContext) -> str:
        """Export context to JSON."""
        return self._serializer.to_json(context)

    def import_json(self, payload: str) -> CalculationContext:
        """Import context from JSON."""
        return self._serializer.from_json(payload)

    def export_binary(self, context: CalculationContext) -> bytes:
        """Export context to binary."""
        return self._serializer.to_binary(context)

    def import_binary(self, payload: bytes) -> CalculationContext:
        """Import context from binary."""
        return self._serializer.from_binary(payload)

    def _publish_update(self, key: str) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(
                CalculationContextUpdatedEvent(payload={"key": key})
            )

    @staticmethod
    def _cache_key(underlying: str, exchange: str, expiry: str) -> str:
        return f"{exchange.upper()}:{underlying.upper()}:{expiry}"
