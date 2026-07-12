# Backtesting Architecture

```mermaid
flowchart TB
    subgraph Input
        A[BacktestRequest]
        B[Historical Market Data]
        C[Strategy]
        D[StrategyContext]
    end

    subgraph Components
        E[Replay Engine]
        F[Execution Simulator]
        G[Backtesting Engine]
        H[Performance Analytics]
    end

    subgraph Portfolio
        I[PortfolioTracker]
    end

    subgraph FrozenEngines
        J[Strategy Context]
        K[Margin / Payoff Results]
    end

    A --> G
    G --> E
    G --> F
    E --> G
    F --> I
    G --> I
    D --> J
    J --> K
    K --> I
    G --> H
    H --> L[BacktestResult]
```

## Component Independence

Each component is independently testable and replaceable:

- **Replay** — no knowledge of execution or analytics
- **Execution** — configurable slippage/fees, no pricing formulas
- **Backtest Engine** — pure orchestration
- **Analytics** — trade log and equity curve only
