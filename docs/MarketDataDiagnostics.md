# Market Data Diagnostics

Temporary diagnostic logging for tracing live market ticks through the OptionDesk Pro pipeline.

## Diagnostic Flow

When `market_data_debug` is enabled in application configuration, ticks are logged once per layer:

```text
[WEBSOCKET]
    ↓
[DISPATCHER]
    ↓
[EVENTBUS]
    ↓
[UI-BRIDGE]
    ↓
[VIEWMODEL]
    ↓
UI Updated
```

Cache reads are logged separately when workspace services query stored ticks:

```text
[CACHE] cache lookup / cache snapshot
```

## Log Prefixes

| Prefix | Layer | When logged |
|--------|-------|-------------|
| `[WEBSOCKET]` | Breeze WebSocket handler | After tick is normalized and enqueued |
| `[DISPATCHER]` | Background dispatcher thread | After tick is written to live cache |
| `[EVENTBUS]` | Event publication | Before `TickReceivedEvent` is published |
| `[UI-BRIDGE]` | Qt event bridge | Before Qt signals are emitted |
| `[VIEWMODEL]` | Market ViewModel | When tick signal is received |
| `[CACHE]` | MarketDataService | On cache lookup or snapshot |
| `[STATUS]` | Reserved for connection/status diagnostics |

## Expected Sequence

For a single tick that reaches the UI, expect one log line per layer in order:

1. `[WEBSOCKET] tick received` — symbol, exchange, LTP, bid, ask, volume, timestamp
2. `[DISPATCHER] tick cached` — same fields plus queue size and tick count
3. `[EVENTBUS] publishing tick events` — concise tick fields
4. `[UI-BRIDGE] forwarding tick to UI` — concise tick fields
5. `[VIEWMODEL] tick received` — concise tick fields

If the sequence stops at a layer, the tick did not propagate beyond that point.

## Log Levels

High-frequency diagnostics use **DEBUG** level to avoid flooding production logs:

- WebSocket ticks
- Dispatcher processing
- EventBus publication
- UI bridge forwarding
- ViewModel receipt
- Cache lookups and snapshots

Diagnostics are suppressed when:

1. `market_data_debug` is `false` in configuration, or
2. The active loguru sink level is above DEBUG

## Configuration

### Application YAML

```yaml
# config/application.yaml
market_data_debug: true
```

### Runtime

The flag is loaded during kernel bootstrap via `configure_market_data_debug()` in `src/app/market_data/diagnostics.py`.

Default value: **true**

### Disable diagnostics

Set in `config/application.yaml` or user config override:

```yaml
market_data_debug: false
```

Or ensure the console/file log level is INFO or higher to suppress DEBUG diagnostics while leaving the flag enabled.

## Field Format

Diagnostics log concise structured fields — not full payload dictionaries:

- `symbol`
- `exchange`
- `ltp`
- `bid`
- `ask`
- `volume`
- `timestamp`

Layer-specific extras:

- **DISPATCHER**: `queue_size`, `tick_count`
- **CACHE**: `symbol_count` (snapshots) or lookup hit/miss

## Implementation

Central helpers in `src/app/market_data/diagnostics.py`:

- `market_data_debug_enabled()` — configuration gate
- `log_market_data_diagnostic()` — generic structured log
- `log_tick_diagnostic()` — tick field extraction and logging

All call sites use these helpers; do not hardcode diagnostic flags elsewhere.
