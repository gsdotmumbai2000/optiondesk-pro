# Live Analytics Event Flow

```text
MarketDataService
    │
    ├── PriceUpdatedEvent
    ├── QuoteUpdatedEvent
    └── OptionUpdatedEvent
            │
            ▼
    LiveAnalyticsService.on_market_event()
            │
            ├──► LiveOptionChainService.on_tick()
            │         └── LiveOptionCache
            │
            ├──► LiveOptionChainUpdatedEvent
            │
            └──► RefreshCoordinator.should_refresh()
                      │
                      ▼ (if allowed)
              CalculationDispatcher.submit()
                      │
                      ▼ (thread pool)
              LiveCalculationPipeline.run()
                      │
                      ├── GreeksUpdatedEvent
                      ├── VolatilityUpdatedEvent
                      ├── ProbabilityUpdatedEvent
                      ├── RiskCalculatedEvent
                      ├── MarginUpdatedEvent
                      ├── PortfolioUpdatedEvent
                      ├── PositionUpdatedEvent
                      └── LiveAnalyticsRefreshedEvent
```

## Event Sources

| Event | Source |
|-------|--------|
| Market tick events | `MarketDataService` via `EventBus` |
| Chain update | `LiveAnalyticsService` |
| Engine analytics | `AnalyticsPublisher` after pipeline run |

## Application Layer

Workspace services read cached analytics via `LiveAnalyticsPort`:

- `MarketWorkspaceService.option_chain()` / `live_analytics()`
- `StrategyWorkspaceService.live_chain_context()`
- `PortfolioWorkspaceService.live_position_analytics()`
- `TradingWorkspaceService.live_trading_analytics()`
- `AIWorkspaceService.live_recommendation_context()`

ViewModels must not subscribe to `MarketDataService` directly.
