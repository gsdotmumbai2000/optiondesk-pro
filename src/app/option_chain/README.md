# Enterprise Option Chain Analytics Engine

The Option Chain Engine analyzes chain liquidity, skew, and open interest metrics.

## Scope

- Liquidity score and put/call ratio
- ATM implied volatility and skew
- Report-ready immutable data models

## Dependencies

- `CalculationContext`, `OptionChainSnapshot`, `GreeksResult`, `VolatilityResult`

## Module Layout

```
src/app/option_chain/
  engine/         # OptionChainEngine, OptionChainAnalyzer
  analytics/      # Liquidity, put/call ratio, skew
  models/         # OptionChainAnalysis, ChainMarketSnapshot
  services/       # OptionChainAnalyticsService
  cache/          # OptionChainCache
  validation/     # OptionChainValidator
  bootstrap.py    # OptionChainProvider
```
