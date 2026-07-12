# Enterprise Margin Engine

The Margin Engine is the single source of margin and capital requirement calculations for OptionDesk Pro.

## Scope

- Initial, exposure, SPAN, and portfolio margin
- Buying power and margin utilization
- Capital requirement and efficiency
- Leverage ratio and margin benefit/offset
- Broker adapter framework (estimated and broker response)
- Margin optimization with reduction suggestions
- Report-ready data models (no UI)

## Dependencies

- `CalculationContext`, `RiskResult`, `PayoffResult`
- Strategy legs and portfolio positions (from payoff module)
- `MarketSnapshot` from market data engine
- Normalized `BrokerMarginResponse` (adapter output)

## Module Layout

```
src/app/margin/
  engine/         # MarginEngine, MarginCalculator, MarginEstimator
  analytics/      # Leg margin, portfolio margin, buying power
  adapters/       # MarginProvider, EstimatedMarginProvider, BrokerMarginProvider
  broker/         # Future broker-specific adapters
  optimization/   # MarginOptimizer, suggestions
  services/       # MarginService, CapitalEfficiencyService
  cache/          # MarginCache
  validation/     # MarginValidator
  bootstrap.py    # MarginProvider
```

## Quick Start

```python
from app.margin import MarginAnalysisRequest, MarginProvider

provider = MarginProvider(event_bus=event_bus)
request = MarginAnalysisRequest(
    context=context,
    legs=legs,
    risk_result=risk_result,
    payoff_result=payoff_result,
    market_snapshot=market_snapshot,
    broker_response=broker_response,  # optional
)
result = provider.service.calculate(request)
optimization = provider.service.optimize(request, result)
```

## Documentation

- [Margin Flow](../../docs/margin/margin-flow.md)
- [Class Diagram](../../docs/margin/class-diagram.md)
- [Sequence Diagram](../../docs/margin/sequence-diagram.md)

## Out of Scope

Strategy engine, backtesting, AI, desktop UI, database.

## Performance

Target: 100-leg strategy margin in under 10 ms.

## Broker Adapters

Broker-specific logic is isolated in `adapters/` and future `broker/` packages. Supported pattern:

| Provider | Description |
|----------|-------------|
| `EstimatedMarginProvider` | Position-based SPAN/exposure estimation |
| `BrokerMarginProvider` | Normalized broker API response |

Future: Breeze, Zerodha, Dhan, Upstox, Fyers.
