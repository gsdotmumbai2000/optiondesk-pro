# Application Flow

## Startup Flow

```mermaid
sequenceDiagram
    participant UI
    participant Provider as ApplicationProvider
    participant Coordinator as ApplicationCoordinator
    participant Sessions as SessionManager

    UI->>Provider: ApplicationProvider(event_bus)
    UI->>Coordinator: start_session(TRADING)
    Coordinator->>Sessions: create()
    Sessions-->>Coordinator: ApplicationSession
    Coordinator-->>UI: ApplicationSession
```

## Command Flow

```mermaid
flowchart LR
    A[UI Action] --> B[ApplicationCommand]
    B --> C[CommandDispatcher]
    C --> D{CommandType}
    D -->|OPEN_STRATEGY| E[StrategyWorkspaceService]
    D -->|RUN_BACKTEST| F[BacktestingWorkspaceService]
    D -->|REFRESH_PORTFOLIO| G[PortfolioWorkspaceService]
    D -->|GENERATE_RECOMMENDATION| H[AIWorkspaceService]
    E & F & G & H --> I[Frozen Engine Provider]
    I --> J[Engine Service]
    J --> K[Result cached in WorkspaceCache]
    K --> L[UI Response]
```

## Query Flow

```mermaid
flowchart LR
    A[UI Query] --> B[ApplicationQuery]
    B --> C[QueryDispatcher]
    C --> D{QueryType}
    D -->|GET_PORTFOLIO| E[PortfolioWorkspaceService]
    D -->|GET_STRATEGY| F[StrategyWorkspaceService]
    D -->|GET_RECOMMENDATIONS| G[AIWorkspaceService]
    E & F & G --> H[QueryResult]
    H --> I[UI]
```

## Event Flow

| Event | Trigger |
|-------|---------|
| `WorkspaceOpenedEvent` | `WorkspaceCoordinator.open_workspace()` |
| `WorkspaceClosedEvent` | `WorkspaceCoordinator.close_workspace()` |
| `StrategyLoadedEvent` | `ApplicationCoordinator.notify_strategy_loaded()` |
| `PortfolioLoadedEvent` | `ApplicationCoordinator.notify_portfolio_loaded()` |
| `BacktestStartedEvent` | `ApplicationCoordinator.notify_backtest_started()` |
| `RecommendationReadyEvent` | `ApplicationCoordinator.notify_recommendation_ready()` |

## Session State

`ApplicationSession` tracks:

- Active workspace
- Per-workspace state (`WorkspaceState`)
- Recent files and strategies
- User preferences
