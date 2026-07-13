# Thread Model

## Threads

| Thread | Role | Blocking? |
|--------|------|-----------|
| Broker WebSocket | Receive ticks | Never blocks UI |
| Market Event Dispatcher | Publish market events | Enqueue only |
| EventBus handlers | `LiveAnalyticsService.on_market_event` | Fast; schedules calc |
| `live-calc-*` pool | `LiveCalculationPipeline.run` | Isolated workers |
| UI (Qt main) | Read caches via workspace services | Never runs engines |

## Flow

```text
WebSocket Thread
    └── enqueue tick
            └── Market Dispatcher Thread
                    └── EventBus.publish
                            └── LiveAnalyticsService (sync handler)
                                    ├── update chain cache
                                    └── CalculationDispatcher.submit
                                            └── ThreadPoolExecutor
                                                    └── engine pipeline
```

## Shutdown

`LiveAnalyticsProvider.stop()`:

1. Unsubscribes from market events (via provider lifecycle)
2. Shuts down `CalculationDispatcher` thread pool
3. Stops `RefreshCoordinator`

## Safety

- All caches use `RLock` or `LruTtlCache` internal locking
- Calculation failures are logged, not propagated to UI thread
- Duplicate in-flight calculations per chain key are suppressed
