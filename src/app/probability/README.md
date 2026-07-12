# Enterprise Probability Engine

The Probability Engine is the single source of probability-of-profit and expected value analytics.

## Scope

- Probability of profit and touch
- Expected value estimation
- Report-ready immutable data models

## Dependencies

- `CalculationContext`, `PricingResult`, `GreeksResult`, `VolatilityResult`
- `OptionChainAnalysis`

## Module Layout

```
src/app/probability/
  engine/         # ProbabilityEngine, ProbabilityCalculator
  analytics/      # POP, expected value
  models/         # ProbabilityResult
  services/       # ProbabilityService
  cache/          # ProbabilityCache
  validation/     # ProbabilityValidator
  bootstrap.py    # ProbabilityProvider
```
