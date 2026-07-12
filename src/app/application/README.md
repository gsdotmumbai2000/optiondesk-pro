# Enterprise Application Services Layer

The Application Services Layer is the **only** interface between the Desktop UI and all business engines in OptionDesk Pro.

## Scope

- Coordinate calls to frozen engines via provider registry
- Manage application sessions and workspace state
- Expose simplified workspace APIs for UI
- Command/query dispatch (CQRS)
- Navigation between workspaces
- Publish UI-facing application events
- Workspace caching

## UI Must Never Call Directly

- Pricing, Greeks, Probability, Risk, Margin engines
- Strategy, Portfolio, Backtesting, Monitor, AI engines
- Broker framework

All access flows through `ApplicationProvider`.

## Workspaces

| Workspace | Service | Capabilities |
|-----------|---------|--------------|
| Trading | `TradingWorkspaceService` | Create/evaluate/optimize/backtest/save/load strategy, AI recommendations |
| Strategy | `StrategyWorkspaceService` | Strategy CRUD, list, templates |
| Portfolio | `PortfolioWorkspaceService` | Load/refresh/monitor portfolio, reports, export |
| Backtesting | `BacktestingWorkspaceService` | Run/pause/resume/stop/replay/export |
| Market | `MarketWorkspaceService` | Watchlist, overview, option chain, scanner, volatility |
| AI | `AIWorkspaceService` | Generate/explain/compare recommendations, history |
| Order | `OrderWorkspaceService` | Order intents (no broker execution) |
| Settings | `SettingsWorkspaceService` | User preferences |

## Module Layout

```
src/app/application/
  services/         # Workspace services
  workspaces/       # Workspace registry
  commands/         # CommandDispatcher
  queries/          # QueryDispatcher
  session/          # SessionManager
  navigation/       # NavigationService
  orchestration/    # ApplicationCoordinator, WorkspaceCoordinator, EngineRegistry
  events/           # UI application events
  models/           # Session, commands, queries, workspace DTOs
  cache/            # WorkspaceCache
  validation/       # ApplicationValidator
  bootstrap.py      # ApplicationProvider
```

## Quick Start

```python
from app.application import ApplicationProvider, WorkspaceType

provider = ApplicationProvider(event_bus=event_bus)
session = provider.coordinator.start_session(WorkspaceType.TRADING)

# Navigate to portfolio workspace
view = provider.navigation.navigate(session.session_id, WorkspaceType.PORTFOLIO)

# Evaluate strategy (UI passes engine request objects through application layer)
evaluation = provider.trading.evaluate_strategy(session.session_id, eval_request)
```

## Documentation

- [Architecture](../../docs/application/architecture.md)
- [Application Flow](../../docs/application/application-flow.md)
- [Workspace Flow](../../docs/application/workspace-flow.md)
- [Sequence Diagram](../../docs/application/sequence-diagram.md)

## Out of Scope

UI rendering, broker order execution, quantitative calculations.

## Performance

Target: workspace response under 100 ms.

## Extensibility

Designed for future REST API, gRPC, Web UI, and Mobile App without changing business engines.
