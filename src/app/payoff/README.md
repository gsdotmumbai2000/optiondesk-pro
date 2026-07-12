# Enterprise Payoff Engine

The Payoff Engine is the single source of expiry payoff, breakeven, and risk-reward analytics for OptionDesk Pro.

## Scope

- Expiry payoff and current PnL across multi-leg strategies
- Payoff curves and breakeven detection
- Maximum gain/loss and risk-reward ratio
- Probability-weighted payoff metrics
- Risk table generation for downstream risk engines
- Report-ready immutable data models (no UI)

## Dependencies

- `CalculationContext`, `PricingResult`, `GreeksResult`
- `VolatilityResult`, `ProbabilityResult`
- Strategy legs and portfolio positions

## Module Layout

```
src/app/payoff/
  engine/         # PayoffEngine, PayoffCalculator
  analytics/      # Expiry payoff, curves, breakevens, risk table
  models/         # StrategyLeg, PortfolioPosition, PayoffResult
  services/       # PayoffService
  cache/          # PayoffCache
  validation/     # PayoffValidator
  providers/      # Cache keys
  bootstrap.py    # PayoffProvider
```

## Quick Start

```python
from app.payoff import PayoffAnalysisRequest, PayoffProvider

provider = PayoffProvider(event_bus=event_bus)
request = PayoffAnalysisRequest(
    context=context,
    pricing_result=pricing_result,
    greeks_result=greeks_result,
    volatility_result=volatility_result,
    probability_result=probability_result,
    legs=legs,
    portfolio=portfolio,
)
result = provider.service.calculate(request)
```

## Out of Scope

Pricing, Greeks, volatility, probability, margin, strategy recognition, desktop UI, database.

## Performance

Target: 100-leg strategy payoff curve in under 10 ms.
