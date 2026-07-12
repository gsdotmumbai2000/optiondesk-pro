# Enterprise Strategy Optimizer

The Strategy Optimizer searches, evaluates, ranks, and recommends option strategies by orchestrating frozen engines.

## Architectural Principle

- **No pricing, Greeks, volatility, payoff, probability, risk, or margin calculations**
- All quantitative work delegated to Strategy Engine and downstream frozen engines
- Optimizer responsibility: generate candidates, evaluate, filter, score, rank, recommend

## Scope

- Candidate generation (single leg, spreads, straddles, iron condors, etc.)
- Search algorithms (brute force implemented; genetic, PSO, etc. as framework)
- Objectives (MAX POP, MIN RISK, DELTA NEUTRAL, etc.)
- Constraints (max loss, max margin, min POP, max legs, etc.)
- Scoring and ranking (Top 10/25/50/custom)
- Filters (capital, liquidity, expiry)
- Optimization cache with history and saved results

## Dependencies

- Strategy Engine (evaluation orchestration)
- All frozen quantitative engines (via Strategy Engine)

## Module Layout

```
src/app/strategy_optimizer/
  engine/         # OptimizerEngine, evaluation port
  generators/     # Candidate strategy generation
  search/         # Brute force + algorithm framework
  objectives/     # Objective weighting
  constraints/    # Constraint checking
  filters/        # Candidate filters
  scoring/        # Score mapping from engine outputs
  ranking/        # Top-N ranking
  services/       # StrategyOptimizer, Search, Ranking, etc.
  cache/          # OptimizationCache
  bootstrap.py    # OptimizerProvider
```

## Quick Start

```python
from app.strategy_optimizer import OptimizationRequest, OptimizerProvider

provider = OptimizerProvider(event_bus=event_bus)
result = provider.service.optimize(request)
print(result.recommendation)
print(result.ranking)
```

## Documentation

- [Architecture Diagram](../../docs/strategy_optimizer/architecture-diagram.md)
- [Sequence Diagram](../../docs/strategy_optimizer/sequence-diagram.md)
- [Optimization Flow](../../docs/strategy_optimizer/optimization-flow.md)

## Performance

Target: 1000 candidate strategies evaluated in under 2 seconds.

## Out of Scope

AI optimization, ML ranking, reinforcement learning, UI, database, broker.
