# Enterprise Backtesting Engine

The Backtesting Engine simulates historical trading sessions by orchestrating four independent components.

## Architecture

| Component | Responsibility |
|-----------|----------------|
| **Replay Engine** | Historical candles, option chains, market events |
| **Execution Simulator** | Orders, slippage, commission, partial fills |
| **Backtesting Engine** | Orchestrates replay, execution, portfolio |
| **Performance Analytics** | Sharpe, Sortino, drawdown, trade statistics |

## Principles

- **No pricing, Greeks, volatility, margin, or payoff formulas**
- Margin and PnL consumed from `StrategyContext` (frozen engines)
- Performance analytics operates on trade log and equity curve only

## Module Layout

```
src/app/backtesting/
  replay/         # ReplayEngine
  execution/      # ExecutionSimulator
  engine/         # BacktestEngine orchestrator
  analytics/      # PerformanceAnalytics
  portfolio/      # PortfolioTracker
  reports/        # Report data models
  services/       # BacktestService, Replay, Execution, Analytics
  cache/          # BacktestCache
  bootstrap.py    # BacktestProvider
```

## Quick Start

```python
from app.backtesting import BacktestProvider, BacktestRequest

provider = BacktestProvider(event_bus=event_bus)
result = provider.service.run(request)
report = provider.service.build_report(result)
```

## Documentation

- [Architecture Diagram](../../docs/backtesting/architecture-diagram.md)
- [Replay Flow](../../docs/backtesting/replay-flow.md)
- [Execution Flow](../../docs/backtesting/execution-flow.md)
- [Sequence Diagram](../../docs/backtesting/sequence-diagram.md)

## Performance

Target: replay 100,000 historical bars in under 5 seconds.

## Out of Scope

Tick replay, order book, paper trading, UI, database, broker.
