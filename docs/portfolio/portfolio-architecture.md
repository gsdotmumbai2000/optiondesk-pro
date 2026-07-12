# Portfolio Architecture

## Overview

The Portfolio Management Engine maintains authoritative portfolio state and produces analytics by orchestrating frozen quantitative engines. It never recomputes pricing, Greeks, volatility, probability, risk, or margin.

## Layers

| Layer | Responsibility |
|-------|----------------|
| Models | Immutable dataclasses for state and results |
| Engine | State mutation and result assembly |
| Services | Orchestration, caching, events |
| Analytics | Adapters from Risk/Margin engines |
| Performance | Return and drawdown from value history |
| Repository | Persistent portfolio aggregates |
| Cache | Latest results, snapshots, history |

## Data Flow

```
Trade Executions / Broker Updates
        │
        ▼
PortfolioStateBuilder ──► Portfolio (updated state)
        │
        ▼
PortfolioEngine ◄── RiskResult, MarginResult, BacktestResult
        │
        ▼
PortfolioResult ──► Cache / Events / Reports
```

## Engine Consumption

| Field | Source |
|-------|--------|
| Greeks Summary | `RiskResult.net_delta/gamma/theta/vega` |
| Risk Summary | `RiskResult.value_at_risk/risk_score/capital_at_risk` |
| Used/Available Margin | `MarginResult.total_margin/available_margin` |
| Performance (backtest) | `BacktestResult.total_return/maximum_drawdown` |

## Extensibility

Designed for future support of:

- Multiple portfolios
- Multiple accounts
- Multiple brokers
- Family and managed accounts

## Performance

- Thread-safe `PortfolioCache` with TTL and history
- In-memory repository with `RLock`
- Incremental state updates via `PortfolioStateBuilder`
