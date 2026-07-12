# Calculation Engine Data Flow

## Overview

```
Market Master ──┐
                ├──► Port Adapters ──► Providers ──► Factory ──► CalculationContext
Market Data  ───┘                                              │
                                                               ▼
                                                         ContextCache
                                                               │
                                                               ▼
                                                    Future Pricing / Greeks Engines
```

## Input Sources (via Ports Only)

| Input | Provider | Port |
|-------|----------|------|
| Spot / Future / Chain | `MarketSnapshotBuilder` | `IMarketDataQueryPort` |
| Lot / Tick / Strike interval | Factory | `IInstrumentSpecificationPort` |
| DTE / TTE | `ExpiryProvider` | `IExpiryCalendarPort` |
| Market open / trade date | `MarketStatusProvider` | `IMarketStatusPort` |
| Interest / dividend | `InterestRateProvider`, `DividendProvider` | internal defaults |
| Volatility | `VolatilityProvider` | chain ATM IV + defaults |
| Clock | `TimeProvider` | internal |

## Normalization Pipeline

1. Raw quotes converted to calculation-owned snapshots (`SpotQuoteSnapshot`, etc.)
2. Prices quantized via `normalize_price`
3. Rates bounded via `normalize_interest_rate`
4. Volatility bounded via `normalize_volatility`
5. ATM strike derived from chain or `atm_strike(spot, interval)`

## Output Contract

`CalculationContext` is the sole input contract for:

- Option pricing engines (future)
- Greeks engines (future)
- Payoff and strategy engines (future)

No downstream module may call broker, database, or market data APIs directly.

## Serialization Flow

```
CalculationContext
    │ asdict + stringify
    ▼
JSON dict / JSON string / base64 binary
    │ decode_context
    ▼
CalculationContext (round-trip)
```

## Event Flow

```
Factory.build ──► CalculationContextCreated
Service.create_context ──► CalculationContextUpdated
Factory validation failure ──► CalculationContextInvalid
```

## Performance Notes

- Single-pass assembly with injected ports
- Immutable dataclasses minimize defensive copies
- Cache keyed by `exchange:underlying:expiry` for O(1) lookup
- Target context creation under 1 ms excluding upstream market data latency
