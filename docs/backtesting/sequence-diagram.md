# Backtesting Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant BacktestService
    participant BacktestValidator
    participant BacktestEngine
    participant ReplayEngine
    participant ExecutionSimulator
    participant PortfolioTracker
    participant StrategyContext
    participant PerformanceAnalytics
    participant BacktestCache
    participant EventBus

    Client->>BacktestService: run(request)
    BacktestService->>BacktestValidator: validate(request)
    BacktestValidator-->>BacktestService: ok
    BacktestService->>EventBus: ReplayStartedEvent
    BacktestService->>BacktestEngine: run(request)
    BacktestEngine->>ReplayEngine: start()
    loop each bar
        BacktestEngine->>ReplayEngine: step_forward()
        ReplayEngine-->>BacktestEngine: ReplayEvent
        BacktestEngine->>ExecutionSimulator: execute(order)
        ExecutionSimulator-->>BacktestEngine: ExecutionResult
        BacktestEngine->>PortfolioTracker: apply_trade()
        BacktestEngine->>StrategyContext: margin / PnL
        StrategyContext-->>PortfolioTracker: engine outputs
    end
    BacktestEngine->>PerformanceAnalytics: analyze(trades, equity)
    PerformanceAnalytics-->>BacktestEngine: PerformanceMetrics
    BacktestEngine-->>BacktestService: BacktestResult
    BacktestService->>BacktestCache: put(key, result)
    BacktestService->>EventBus: BacktestCompletedEvent
    BacktestService-->>Client: BacktestResult
```

## Data Flow

1. Replay provides historical prices (no pricing engine)
2. Execution simulates fills with slippage and fees
3. Portfolio tracks positions and cash
4. Margin and unrealized PnL from `StrategyContext` (frozen engines)
5. Analytics computes performance metrics from trade log and equity curve
