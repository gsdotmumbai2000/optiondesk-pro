"""Live market data documentation."""

# Live Market Data Engine

Feature 25 delivers live ICICI Breeze market data through a single `MarketDataService` API.

## Architecture

```text
Broker (Breeze WebSocket)
  → WebSocketManager
  → TickDispatcher
  → TickCache
  → EventBus (TickReceived)
  → MarketDataEngine (normalize/cache)
  → MarketDataService
  → MarketWorkspaceService
  → ViewModels
  → UI
```

## Components

| Component | Path |
|-----------|------|
| `LiveMarketDataProvider` | `market_data/live/live_provider.py` |
| `MarketDataService` | `market_data/services/market_data_service.py` |
| `MarketDataSubscriptionManager` | `market_data/live/subscription_manager.py` |
| `TickDispatcher` | `market_data/live/tick_dispatcher.py` |
| `WebSocketManager` | `market_data/live/websocket_manager.py` |
| `ReconnectManager` | `market_data/live/reconnect_manager.py` |
| `HeartbeatMonitor` | `market_data/live/heartbeat_monitor.py` |
| `MarketStatusDetector` | `market_data/live/market_status_detector.py` |
| `TickCache` | `market_data/live/tick_cache.py` |

## Usage

All modules must consume prices via `MarketDataService`:

```python
service = market_data_provider.service
service.subscribe("NIFTY", "NSE")
price = service.latest_price("NIFTY", "NSE")
status = service.market_status()
```

## Events

- `TickReceivedEvent`
- `MarketOpenedEvent` / `MarketClosedEvent`
- `SubscriptionAddedEvent` / `SubscriptionRemovedEvent`
- `BrokerConnectedEvent` / `BrokerDisconnectedEvent` (broker layer)

## Connection State Machine

Market data uses `MarketDataConnectionStateMachine` with states:

- **Disconnected** — no broker subscriptions
- **Connecting** — activating feed after `BrokerConnected`
- **Connected** — live subscriptions and tick processing enabled
- **Reconnecting** — pausing feed on disconnect
- **Failed** — authentication or activation failure

Watchlist symbols are loaded as **pending** subscriptions at startup.
Broker `subscribe_quotes()` is called only when state is **Connected**.
On disconnect, active subscriptions are removed but pending watchlist and
cached (stale) prices are retained.
