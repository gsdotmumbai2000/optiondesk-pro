# Enterprise Position Monitor & Alert Engine

The Position Monitor & Alert Engine continuously monitors live positions and generates alerts, recommendations, and risk notifications for OptionDesk Pro.

## Scope

- Position monitoring (open positions, portfolio, cash, margin, PnL)
- Alert generation with configurable rules and priorities
- Threshold monitoring against engine outputs
- Adjustment and exit suggestion framework (no AI)
- Risk notifications via alert system
- Configurable monitoring scheduler
- Thread-safe caching

## Does NOT Calculate

- Pricing
- Greeks
- Probability
- Payoff
- Margin

All quantitative values are consumed from frozen engines.

## Dependencies

- `PortfolioResult` from portfolio management engine
- `RiskResult` from risk engine
- `MarginResult` from margin engine
- `ProbabilityResult` from probability engine
- `StrategyEvaluation` from strategy engine
- `MarketSnapshot` and market data events

## Module Layout

```
src/app/monitor/
  engine/           # MonitorEngine orchestrator
  models/           # Immutable domain models
  rules/            # Built-in and custom alert rules
  triggers/         # Threshold trigger evaluation
  alerts/           # Alert factory and manager
  recommendations/  # Framework suggestions (no AI)
  analytics/        # Adapters, health score, position analyzer
  scheduler/        # Monitoring interval scheduler
  services/         # PositionMonitor, Alert, Rule, Recommendation, Notification
  cache/            # MonitorCache
  validation/       # MonitorValidator
  serialization/    # JSON/binary serialization
  bootstrap.py      # MonitorProvider
```

## Quick Start

```python
from app.monitor import MonitorAnalysisRequest, MonitorProvider

provider = MonitorProvider(event_bus=event_bus)
session = provider.service.start_monitoring("portfolio-id")

request = MonitorAnalysisRequest(
    session_id=session.session_id,
    portfolio_result=portfolio_result,
    risk_result=risk_result,
    margin_result=margin_result,
    probability_result=probability_result,
    strategy_evaluation=strategy_evaluation,
    market_snapshot=market_snapshot,
)
result = provider.service.evaluate(request)
```

## Documentation

- [Architecture](../../docs/monitor/architecture.md)
- [Monitoring Flow](../../docs/monitor/monitoring-flow.md)
- [Alert Flow](../../docs/monitor/alert-flow.md)
- [Sequence Diagram](../../docs/monitor/sequence-diagram.md)

## Out of Scope

AI recommendations, email/SMS/push delivery, broker logic, UI rendering.

## Performance

Target: monitor 1,000 positions in under one second.
