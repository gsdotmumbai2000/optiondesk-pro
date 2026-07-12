# Execution Flow

```mermaid
flowchart TD
    A[OrderRequest] --> B[ExecutionSimulator]
    B --> C{Order Type}
    C -->|MARKET| D[Apply Slippage]
    C -->|LIMIT| D
    C -->|STOP| D
    D --> E[Partial Fill?]
    E --> F[Compute Fees]
    F --> G[Commission + Brokerage + Exchange]
    G --> H[Apply Latency]
    H --> I[ExecutionResult]
    I --> J[Trade]
    J --> K[PortfolioTracker]
    K --> L[TradeExecutedEvent]
```

## Execution Model

| Parameter | Default |
|-----------|---------|
| Slippage | 0.05% |
| Commission | ₹20 per trade |
| Brokerage | 0.03% |
| Exchange charges | 0.01% |
| Latency | 50ms |
| Partial fill | Enabled |

## Order Types

- Market — immediate fill with slippage
- Limit — framework ready
- Stop — framework ready

No broker-specific logic; fully configurable via `ExecutionConfig`.
