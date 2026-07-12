# Enterprise Greeks Engine

The Greeks Engine is the single source of option sensitivity analytics for OptionDesk Pro.

## Scope

- Black-Scholes delta, gamma, theta, vega, rho
- Second-order Greeks: vanna, charm, vomma
- Input validation and structured `GreeksResult` output

## Dependencies

- `CalculationContext`, `OptionContract`, `PricingResult`

## Module Layout

```
src/app/greeks/
  engine/         # GreeksEngine, GreeksCalculator
  analytics/      # Black-Scholes Greeks formulas
  models/         # GreeksResult
  services/       # GreeksService
  cache/          # GreeksCache
  validation/     # GreeksValidator
  bootstrap.py    # GreeksProvider
```

## Quick Start

```python
from app.greeks import GreeksProvider

provider = GreeksProvider(event_bus=event_bus)
result = provider.service.calculate_greeks(context, contract, pricing_result)
```
