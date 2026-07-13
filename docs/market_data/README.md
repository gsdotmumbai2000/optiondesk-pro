# Enterprise Live Market Data Engine

The Enterprise Live Market Data Engine is the **single source of truth** for all live market data in OptionDesk Pro. Every module consumes prices exclusively through `MarketDataService`.

## Architecture

```text
Breeze Broker (existing WebSocket)
        │
        ▼
WebSocketService          (websocket thread)
        │
        ▼
EventDispatcher           (background dispatcher thread)
        │
        ├──► MarketCacheService   (thread-safe LRU + TTL)
        │
        └──► EventBus
                ├── PriceUpdated
                ├── QuoteUpdated
                ├── OptionUpdated
                ├── FutureUpdated
                ├── ConnectionEstablished / ConnectionLost
                └── ReconnectStarted / ReconnectCompleted
        │
        ▼
MarketDataService         (application API)
        │
        ▼
Workspace Services / ViewModels
```

## Module Layout

| Package | Responsibility |
|---------|----------------|
| `engine/` | `LiveMarketDataEngine` entry point |
| `websocket/` | Single connection, heartbeat, state machine |
| `subscriptions/` | Subscribe, unsubscribe, bulk, resubscribe |
| `dispatcher/` | Non-blocking tick queue and event publish |
| `cache/` | Live tick cache + normalized market cache |
| `providers/` | `LiveMarketDataProvider` orchestrator |
| `services/` | Public service APIs and bundle |
| `events/` | Enterprise market data events |
| `statistics/` | Tick throughput metrics |
| `validation/` | Subscription validation |

## Services

- **MarketDataService** — prices, ticks, watchlist, connection status
- **SubscriptionService** — pending/active subscription lifecycle
- **WebSocketService** — broker WebSocket handler attachment
- **ReconnectService** — exponential backoff and recovery
- **MarketCacheService** — LRU, expiration, snapshot retrieval

## Threading

| Thread | Role |
|--------|------|
| WebSocket (broker SDK) | Receives raw ticks, enqueues only |
| `md-dispatcher` | Cache update + event publish |
| `md-heartbeat` | Stale feed detection |
| `md-reconnect` | Backoff recovery |
| UI (Qt main) | Reads cache via `MarketDataService` only |

Target throughput: **5000 ticks/sec** without blocking UI.

## Bootstrap

```python
from app.market_data.bootstrap import MarketDataProvider

provider = MarketDataProvider(broker, data_directory, event_bus)
provider.start()
service = provider.service  # MarketDataService
bundle = provider.bundle    # full service bundle
```

## Rules

- Do **not** call Breeze WebSocket from other modules.
- Reuse existing Breeze broker authentication and session handling.
- Subscriptions activate only after broker connection is established.

See also:

- [Sequence Diagram](sequence-diagram.md)
- [Connection Lifecycle](connection-lifecycle.md)
- [Subscription Lifecycle](subscription-lifecycle.md)
