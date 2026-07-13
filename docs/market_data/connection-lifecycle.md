# Connection Lifecycle

## States

| State | Description |
|-------|-------------|
| `Disconnected` | No broker session; subscriptions queued only |
| `Connecting` | Broker ready; activating WebSocket and subscriptions |
| `Connected` | Live feed active; ticks dispatched |
| `Reconnecting` | Broker lost; feed paused, pending watchlist retained |
| `Failed` | Authentication or activation failed |

## Lifecycle

```text
[Disconnected]
      │ BrokerConnected / AuthenticationSucceeded
      ▼
[Connecting] ──activate──► WebSocket.connect()
      │                    Subscription.activate_pending()
      │                    Heartbeat.start()
      ▼
[Connected] ──ticks──► EventDispatcher ──► Cache + EventBus
      │
      │ BrokerDisconnected
      ▼
[Reconnecting] ──pause──► deactivate_all(), websocket.disconnect()
      │
      ▼
[Disconnected]  (pending watchlist preserved, cache stale OK)

Stale heartbeat while Connected:
      ReconnectService ──backoff──► websocket.connect() + resubscribe_all()
      Events: ReconnectStarted → ReconnectCompleted
```

## Events

| Event | When |
|-------|------|
| `ConnectionEstablishedEvent` | Feed activated after broker connect |
| `ConnectionLostEvent` | Broker disconnect detected |
| `ReconnectStartedEvent` | Reconnect or recovery begins |
| `ReconnectCompletedEvent` | WebSocket and subscriptions restored |

## Heartbeat

- Interval: 30 seconds
- Stale threshold: 120 seconds without ticks
- Stale feed triggers `ReconnectService` with exponential backoff: 1, 2, 4, 8, 16, 30 seconds

## Thread Safety

Connection state transitions are guarded by `RLock`. WebSocket callbacks enqueue only; they never touch UI or heavy engine work directly.
