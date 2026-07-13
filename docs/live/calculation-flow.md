# Calculation Flow

## Pipeline Order

The live pipeline mirrors `EngineOrchestrator` dependency order:

```text
1. CalculationContext      (CalculationContextService)
2. OptionChainSnapshot     (LiveOptionChain → ChainBuilder)
3. Pricing                 (ATM contract)
4. Greeks
5. Volatility
6. Option Chain Analytics
7. Probability (POP)
8. Payoff
9. Risk
10. Margin
```

## Input Construction

| Input | Builder |
|-------|---------|
| Calculation context | `LiveContextBuilder.build_context()` |
| Option chain snapshot | `ChainBuilder.to_snapshot()` |
| Market snapshots | `LiveContextBuilder.build_*_snapshot()` |
| Engine bundle | `build_engine_bundle(event_bus)` |

## Output

`LiveAnalyticsSnapshot` stored in:

- `LiveGreeksCache` — greeks results
- `LiveRiskCache` — full analytics snapshot
- `LivePortfolioCache` — portfolio/position greeks

## Validation

Before caching:

- `TickValidator` — tick integrity
- `ChainValidator` — chain consistency
- `FreshnessValidator` — timestamp ordering and staleness

## Performance

- Deduped dispatch per chain key in `CalculationDispatcher`
- Configurable debounce via `RefreshCoordinator`
- Target: 1000 contracts, 5000 ticks/sec ingress with non-blocking UI
