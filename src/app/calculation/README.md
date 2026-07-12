# Calculation Engine

The Enterprise Calculation Engine prepares immutable `CalculationContext` objects for all downstream pricing, Greeks, and risk modules. It does not perform option pricing or Greeks itself.

## Responsibilities

- Read market inputs through injected ports (never direct broker, database, or market data access)
- Validate and normalize inputs
- Build immutable `CalculationContext` instances
- Cache latest and previous contexts
- Serialize contexts for export/import
- Publish lifecycle events

## Module Layout

```
src/app/calculation/
  context/          # CalculationContext
  engine/           # CalculationEngine entry point
  factory/          # CalculationContextFactory, snapshot builder
  models/           # configuration, snapshots, enums
  providers/        # rate, vol, expiry, status providers + port adapters
  services/         # context service, cache, serializer, validator
  validation/       # ContextValidator
  utilities/        # time, strike, normalize helpers
  exceptions/       # calculation-specific errors
  bootstrap.py      # CalculationProvider wiring
```

## Quick Start

```python
from app.calculation.bootstrap import CalculationProvider

provider = CalculationProvider.from_services(
    market_data_query=market_data_engine.query,
    instrument_service=market_provider.instrument_service,
    expiry_service=market_provider.expiry_service,
    calendar_service=market_provider.calendar_service,
    event_bus=event_bus,
)

context = provider.engine.create_context("NIFTY", "NSEFO", "09-Jul-2026")
```

## Design Rules

- Pure domain logic only
- No UI, SQL, broker APIs, or repository access inside calculation code
- All downstream calculations must consume `CalculationContext`
- Context creation target: under 1 ms with immutable, thread-safe cache

## Events

| Event | When |
|-------|------|
| `CalculationContextCreated` | Valid context built |
| `CalculationContextUpdated` | Cache updated |
| `CalculationContextInvalid` | Validation failed |

## Documentation

- [Class Diagram](../../docs/calculation/class-diagram.md)
- [Sequence Diagram](../../docs/calculation/sequence-diagram.md)
- [Context Lifecycle](../../docs/calculation/context-lifecycle.md)
- [Data Flow](../../docs/calculation/data-flow.md)
