# Portfolio Flow

```mermaid
flowchart TD
    A[Strategy Legs / Portfolio Positions] --> B[Resolved Legs]
    B --> C[Greeks Aggregation]
    B --> D[Exposure Calculator]
    B --> E[Stress Runner]
    B --> F[Scenario Engine]
    C --> G[Net Greeks]
    D --> H[PortfolioExposure]
    E --> I[StressTestResults]
    F --> J[ScenarioRanking]
    G --> K[RiskResult]
    H --> K
    I --> K
    K --> L[PortfolioReport]
    L --> M[RiskSummary]
    L --> N[ExposureSummary]
    L --> O[VaRReport]
    L --> P[StressReport]
```

## Exposure Dimensions

| Dimension | Description |
|-----------|-------------|
| Underlying | Notional and weight per underlying symbol |
| Expiry | Exposure grouped by expiration date |
| Option Type | Call vs put exposure |
| Sector | Underlying grouping (sector label) |

## Concentration

Herfindahl index across leg notionals measures portfolio concentration.

## Limit Checking

Optional `RiskLimitConfig` enables warnings for:

- Maximum delta, gamma, vega
- Maximum loss, margin, position size
- Maximum capital exposure
