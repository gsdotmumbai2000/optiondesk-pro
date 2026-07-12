# Calculation Context Lifecycle

## States

1. **Requested** — Client asks `CalculationEngine.create_context`
2. **Assembled** — Factory gathers provider inputs and builds snapshots
3. **Validated** — `ContextValidator` checks expiry, rates, prices, and timestamps
4. **Published** — `CalculationContextCreated` event emitted
5. **Cached** — Latest context stored; prior context rotated to previous slot
6. **Consumed** — Downstream pricing/Greeks engines read immutable context
7. **Expired** — TTL or explicit `expire_context` removes cache entry

## Immutability

`CalculationContext` is a frozen dataclass. Updates always produce a new instance. The cache retains:

- **Latest** — most recent valid context per `exchange:underlying:expiry` key
- **Previous** — prior context for comparison

## Versioning

Each context carries `version: ContextVersion`. Serialization embeds the schema version to support forward-compatible import/export.

## Invalid Paths

| Failure | Exception | Event |
|---------|-----------|-------|
| Missing quote | `MissingMarketDataException` | — |
| Bad expiry format | `InvalidExpiryException` | — |
| Failed validation | `InvalidContextException` | `CalculationContextInvalid` |

## Cache TTL

Default TTL is 300 seconds. Expired entries are purged on read. Explicit `expire_context` clears both latest and previous slots.

## Comparison

`compare_contexts` reports material deltas between latest and previous:

- `spot_price_changed`
- `volatility_changed`
- `days_to_expiry_changed`

## Thread Safety

Pure calculation logic has no internal threading. `ContextCache` uses an `RLock` for concurrent read/write safety.
