# Calculation Engine Class Diagram

```mermaid
classDiagram
    class CalculationEngine {
        +create_context()
        +get_latest_context()
        +get_previous_context()
        +compare_contexts()
    }

    class CalculationContextService {
        +create_context()
        +get_latest()
        +get_previous()
        +compare_contexts()
        +export_json()
        +import_json()
    }

    class CalculationContextFactory {
        +build()
    }

    class ContextValidator {
        +validate()
    }

    class ContextCache {
        +put()
        +get_latest()
        +get_previous()
        +compare()
        +expire()
    }

    class ContextSerializer {
        +to_json()
        +from_json()
        +to_binary()
        +from_binary()
    }

    class CalculationContext {
        <<immutable>>
        +underlying
        +spot_price
        +volatility
        +days_to_expiry
        +option_chain_snapshot
    }

    class IMarketDataQueryPort {
        <<interface>>
        +get_spot()
        +get_future()
        +get_option_chain()
    }

    class IInstrumentSpecificationPort {
        <<interface>>
        +get_lot_size()
        +get_tick_size()
        +get_strike_interval()
    }

    class IExpiryCalendarPort {
        <<interface>>
        +calculate_dte()
        +calculate_tte_seconds()
    }

    class IMarketStatusPort {
        <<interface>>
        +is_market_open()
        +trade_date()
    }

    CalculationEngine --> CalculationContextService
    CalculationContextService --> CalculationContextFactory
    CalculationContextService --> ContextCache
    CalculationContextService --> ContextSerializer
    CalculationContextFactory --> ContextValidator
    CalculationContextFactory --> IMarketDataQueryPort
    CalculationContextFactory --> IInstrumentSpecificationPort
    CalculationContextFactory --> IExpiryCalendarPort
    CalculationContextFactory --> IMarketStatusPort
    CalculationContextFactory ..> CalculationContext : creates
```

## Provider Layer

```mermaid
classDiagram
    class InterestRateProvider
    class DividendProvider
    class VolatilityProvider
    class ExpiryProvider
    class MarketStatusProvider
    class TimeProvider
    class UnderlyingProvider

    CalculationContextFactory --> InterestRateProvider
    CalculationContextFactory --> DividendProvider
    CalculationContextFactory --> VolatilityProvider
    CalculationContextFactory --> ExpiryProvider
    CalculationContextFactory --> MarketStatusProvider
    CalculationContextFactory --> TimeProvider
    CalculationContextFactory --> UnderlyingProvider
```

## Port Adapters

Frozen upstream modules are accessed only through adapters at bootstrap time:

- `MarketDataQueryPortAdapter` → `MarketDataQueryService`
- `InstrumentSpecificationPortAdapter` → `InstrumentService`
- `ExpiryCalendarPortAdapter` → `ExpiryManager`
- `MarketStatusPortAdapter` → `MarketCalendarService`
