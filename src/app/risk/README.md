# Enterprise Risk Engine

The Risk Engine is the single source of quantitative risk analysis for OptionDesk Pro.

## Scope

- Portfolio Greeks aggregation (delta through vomma)
- Value at Risk (historical, parametric, variance-covariance) at 95% and 99%
- Expected Shortfall (CVaR) and tail loss
- Stress testing (price, IV, time, rate, combined)
- Risk limits with warnings
- Portfolio exposure breakdown
- Scenario engine (single, multiple, comparison, ranking)
- Report data models (no UI)

## Dependencies

- `CalculationContext`, `PricingResult`, `GreeksResult`, `VolatilityResult`
- `ProbabilityResult`, `PayoffResult`
- Strategy legs and portfolio positions (from payoff module)
- `MarketSnapshot` from market data engine

## Module Layout

```
src/app/risk/
  engine/         # RiskEngine, PortfolioRiskCalculator, VaR, Stress
  analytics/      # Greeks, VaR, CVaR, drawdown, risk score
  portfolio/      # Exposure calculator
  stress/         # Stress scenarios and runner
  scenarios/      # Scenario engine
  limits/         # Limit checker
  reports/        # Report data models
  services/       # RiskService, VaRService, StressTestService, etc.
  cache/          # RiskCache
  validation/     # RiskValidator
  bootstrap.py    # RiskProvider
```

## Quick Start

```python
from app.risk import RiskAnalysisRequest, RiskProvider

provider = RiskProvider(event_bus=event_bus)
request = RiskAnalysisRequest(
    context=context,
    pricing_result=pricing_result,
    greeks_result=greeks_result,
    volatility_result=volatility_result,
    probability_result=probability_result,
    payoff_result=payoff_result,
    legs=legs,
    market_snapshot=market_snapshot,
)
result = provider.service.calculate(request)
report = provider.service.build_report(result)
```

## Documentation

- [Risk Flow](../../docs/risk/risk-flow.md)
- [Portfolio Flow](../../docs/risk/portfolio-flow.md)
- [Class Diagram](../../docs/risk/class-diagram.md)
- [Sequence Diagram](../../docs/risk/sequence-diagram.md)

## Out of Scope

Strategy engine, margin engine, backtesting, AI, UI rendering.

## Performance

Target: 100-position risk analysis in under 10 ms.
