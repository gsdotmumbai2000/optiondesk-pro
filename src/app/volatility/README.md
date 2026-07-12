# Enterprise Volatility Engine

The Volatility Engine is the single source of implied, realized, and historical volatility analytics for OptionDesk Pro.

## Scope

- Implied and annualized volatility
- Realized and historical volatility
- Expected move and IV percentile
- Report-ready immutable data models

## Dependencies

- `CalculationContext`, `PricingResult`, `GreeksResult`
- `OptionChainSnapshot`, market and historical snapshots

## Module Layout

```
src/app/volatility/
  engine/         # VolatilityEngine, VolatilityCalculator
  analytics/      # IV, realized vol, expected move
  models/         # VolatilityResult, snapshots
  services/       # VolatilityService
  cache/          # VolatilityCache
  validation/     # VolatilityValidator
  bootstrap.py    # VolatilityProvider
```
