# Enterprise Live Option Chain & Real-Time Analytics Engine

The Live Analytics Engine consumes **MarketDataService events only** and continuously updates option chain state and derived analytics by orchestrating frozen quantitative engines.

## Architecture

```text
MarketDataService (EventBus)
        │
        ▼
LiveOptionChainService
        │
        ▼
RefreshCoordinator
        │
        ▼
CalculationDispatcher (thread pool)
        │
        ▼
LiveCalculationPipeline
   ├── Pricing Engine
   ├── Greeks Engine
   ├── Volatility Engine
   ├── Option Chain Engine
   ├── Probability Engine
   ├── Payoff Engine
   ├── Risk Engine
   └── Margin Engine
        │
        ▼
Live Analytics Caches + EventBus
        │
        ▼
Application Workspace Services
```

## Module Layout

| Package | Responsibility |
|---------|----------------|
| `option_chain/` | Aggregate ticks into live chains |
| `calculations/` | Build context and run engine pipeline |
| `dispatcher/` | Background calculation thread pool |
| `refresh/` | Configurable refresh policy |
| `cache/` | Thread-safe live caches |
| `synchronization/` | Subscriber notifications |
| `analytics/` | Event publishing |
| `services/` | Public service APIs |

## Services

- **LiveOptionChainService** — maintain live option chain from ticks
- **CalculationDispatcher** — non-blocking calculation jobs
- **LiveAnalyticsService** — orchestrate refresh and caching
- **RefreshCoordinator** — EveryTick / 250ms / 500ms / 1s / 5s / Manual
- **SynchronizationService** — notify chain subscribers

## Refresh Modes

| Mode | Behavior |
|------|----------|
| `EveryTick` | Recalculate on every qualifying tick |
| `250ms` / `500ms` / `1s` / `5s` | Debounced refresh |
| `Manual` | Refresh only on `request_refresh()` |

## Bootstrap

```python
from app.live.bootstrap import LiveAnalyticsProvider

provider = LiveAnalyticsProvider(event_bus, market_data_service, engines)
provider.start()
analytics = provider.service
```

Wired automatically in `ApplicationProvider` when market data is configured.

## Rules

- No direct Breeze access
- No modifications to frozen quant engines
- ViewModels consume live analytics via workspace services only

See also:

- [Event Flow](event-flow.md)
- [Sequence Diagram](sequence-diagram.md)
- [Calculation Flow](calculation-flow.md)
- [Thread Model](thread-model.md)
