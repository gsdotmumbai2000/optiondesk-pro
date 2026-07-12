# Enterprise Portfolio Management Engine

The Portfolio Management Engine is the single source of truth for all portfolios in OptionDesk Pro.

## Scope

- Portfolio state (cash, holdings, positions, orders, transactions)
- Position lifecycle (open, close, partial, reverse, scale, roll)
- Performance analytics (returns, drawdown, CAGR, ROC)
- Allocation breakdown (asset, underlying, capital)
- Report data models (no UI)
- Thread-safe caching and in-memory repository

## Does NOT Calculate

- Pricing
- Greeks
- Volatility
- Probability
- Risk
- Margin

These are consumed from frozen engines (`RiskResult`, `MarginResult`, `StrategyEvaluation`, `BacktestResult`).

## Dependencies

- `RiskResult` from risk engine
- `MarginResult` from margin engine
- `BacktestResult` from backtesting engine
- `StrategyEvaluation` from strategy engine
- `MarketSnapshot` from market data engine
- Trade executions and broker position updates

## Module Layout

```
src/app/portfolio/
  engine/         # PortfolioEngine, state builder
  models/         # Immutable domain models
  services/       # PortfolioService and sub-services
  repositories/   # In-memory portfolio store
  analytics/      # Adapters and allocation
  performance/    # Returns, drawdown, CAGR
  holdings/       # Holding aggregator
  positions/      # Position lifecycle manager
  transactions/   # Transaction ledger
  cash/           # Cash manager
  events/         # Portfolio lifecycle events
  cache/          # Thread-safe PortfolioCache
  validation/     # PortfolioValidator
  serialization/  # JSON/binary serialization
  reports/        # Report data models
  bootstrap.py    # PortfolioProvider
```

## Quick Start

```python
from decimal import Decimal
from app.portfolio import PortfolioAnalysisRequest, PortfolioProvider

provider = PortfolioProvider(event_bus=event_bus)
portfolio = provider.service.create_portfolio("Main", Decimal("100000"))

request = PortfolioAnalysisRequest(
    portfolio_id=portfolio.portfolio_id,
    risk_result=risk_result,
    margin_result=margin_result,
    trade_executions=trades,
)
result = provider.service.calculate(request)
report = provider.service.build_report(result)
```

## Documentation

- [Portfolio Architecture](../../docs/portfolio/portfolio-architecture.md)
- [Class Diagram](../../docs/portfolio/class-diagram.md)
- [Sequence Diagram](../../docs/portfolio/sequence-diagram.md)
- [Portfolio Lifecycle](../../docs/portfolio/portfolio-lifecycle.md)

## Out of Scope

Broker connectivity, pricing formulas, Greeks formulas, UI rendering.

## Performance

Target: 10,000 positions across 100 portfolios with fast incremental updates.
