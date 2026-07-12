"""Calculation engine bootstrap."""

from app.calculation.engine.calculation_engine import CalculationEngine
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.providers.adapters import (
    ExpiryCalendarPortAdapter,
    InstrumentSpecificationPortAdapter,
    MarketDataQueryPortAdapter,
    MarketStatusPortAdapter,
)
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.ports import (
    IExpiryCalendarPort,
    IInstrumentSpecificationPort,
    IMarketDataQueryPort,
    IMarketStatusPort,
)
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.calculation.services.context_cache import ContextCache
from app.calculation.services.context_service import CalculationContextService
from app.calculation.services.context_serializer import ContextSerializer
from app.events.event_bus import EventBus


class CalculationProvider:
    """Wire calculation engine dependencies."""

    def __init__(
        self,
        market_data: IMarketDataQueryPort,
        instruments: IInstrumentSpecificationPort,
        expiry_calendar: IExpiryCalendarPort,
        market_status: IMarketStatusPort,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize calculation provider."""
        expiry_provider = ExpiryProvider(expiry_calendar)
        factory = CalculationContextFactory(
            market_data,
            instruments,
            expiry_provider,
            InterestRateProvider(),
            DividendProvider(),
            VolatilityProvider(),
            MarketStatusProvider(market_status, TimeProvider()),
            event_bus=event_bus,
        )
        service = CalculationContextService(
            factory,
            ContextCache(),
            ContextSerializer(),
            event_bus,
        )
        self.engine = CalculationEngine(service)

    @classmethod
    def from_services(
        cls,
        *,
        market_data_query: object,
        instrument_service: object,
        expiry_service: object,
        calendar_service: object,
        event_bus: EventBus | None = None,
    ) -> "CalculationProvider":
        """Build provider from frozen upstream services."""
        return cls(
            MarketDataQueryPortAdapter(market_data_query),
            InstrumentSpecificationPortAdapter(instrument_service),
            ExpiryCalendarPortAdapter(expiry_service),
            MarketStatusPortAdapter(calendar_service),
            event_bus=event_bus,
        )
