# Enterprise Strategy Engine

The Strategy Engine is the orchestration layer for all option strategies in OptionDesk Pro.

## Architectural Principle

- Strategies are **collections of legs**, not hardcoded formulas
- **No pricing, Greeks, margin, payoff, or probability calculations** in this module
- All quantitative work is delegated to frozen engines
- Strategy recognition is for **display, reporting, and templates only**

## Scope

- Strategy builder (unlimited legs, clone, modify)
- Engine orchestration (Pricing → Greeks → Volatility → Chain → Probability → Payoff → Risk → Margin)
- Strategy recognition (30+ patterns)
- Analysis aggregation and scoring
- Comparison and ranking
- Templates (built-in + custom JSON import/export)
- Optimization framework (placeholder)
- In-memory repository and cache

## Dependencies (Consumed, Not Modified)

- Pricing, Greeks, Volatility, Option Chain, Probability, Payoff, Risk, Margin engines

## Module Layout

```
src/app/strategy/
  engine/         # StrategyEngine, EngineOrchestrator, EngineBundle
  models/         # Strategy, StrategyContext, StrategyEvaluation
  builders/       # StrategyBuilder, leg converter
  recognition/    # Pattern recognizer (display only)
  templates/      # Built-in templates
  analytics/      # Analysis aggregator, scoring (maps engine outputs)
  comparison/     # Compare and rank evaluations
  optimization/   # Framework placeholder
  services/       # StrategyService, EvaluationService, etc.
  cache/          # StrategyCache
  repository/     # In-memory strategy store
  serialization/  # JSON/binary
  bootstrap.py    # StrategyProvider
```

## Quick Start

```python
from app.strategy import StrategyProvider, StrategyEvaluationRequest

provider = StrategyProvider(event_bus=event_bus)
strategy = provider.service.builder.add_leg(leg).build()
provider.service.create(strategy)

request = StrategyEvaluationRequest(
    strategy=strategy,
    calculation_context=context,
    option_contract=contract,
    option_chain=option_chain,
    market_snapshot=market_snapshot,
    chain_market_snapshot=chain_snapshot,
    volatility_market_snapshot=vol_snapshot,
    historical_data=historical_data,
)
evaluation = provider.service.evaluate(request)
```

## Documentation

- [Strategy Lifecycle](../../docs/strategy/strategy-lifecycle.md)
- [Class Diagram](../../docs/strategy/class-diagram.md)
- [Sequence Diagram](../../docs/strategy/sequence-diagram.md)

## Out of Scope

Backtesting, AI, desktop UI, database, broker-specific logic.

## Performance

Target: 100 strategy evaluations per second (batch mode).
