# Recommendation Flow

## End-to-End Pipeline

```mermaid
flowchart LR
    A[RecommendationAnalysisRequest] --> B[Validate Inputs]
    B --> C[Aggregate Engine Context]
    C --> D[Evaluate Rules]
    D --> E[Match Rules]
    E --> F[Build Evidence]
    F --> G[Build Explanation]
    G --> H[Score Recommendation]
    H --> I[Attach Alternatives]
    I --> J[Validate Output]
    J --> K[Cache + Memory]
    K --> L[Publish Event]
    L --> M[RecommendationBatchResult]
```

## Rule Evaluation

| Condition | Engine Source | Recommendation |
|-----------|---------------|----------------|
| Delta exceeds | RiskResult / Portfolio greeks | Increase Hedge |
| Margin utilization exceeds | MarginResult | Reduce Margin |
| POP below | ProbabilityResult | Position Adjustment |
| Risk score exceeds | RiskResult | Risk Reduction |
| Loss exceeds | PortfolioResult PnL | Reduce Loss |
| Health score below | MonitorResult | Risk Reduction |

## Input Requirements

Minimum: `session_id` + `PortfolioResult`

Optional enrichments improve recommendation quality:

- `RiskResult` — greeks and risk thresholds
- `MarginResult` — margin optimization rules
- `ProbabilityResult` — POP-based adjustments
- `StrategyEvaluation` — strategy context in prompts
- `OptimizationResult` — alternative strategies
- `MonitorResult` — health and alert context
- `MarketSnapshot` — market summary prompts
- `OptionChainAnalysis` — chain context
- `VolatilityResult` — volatility context

## Output Selection

`RecommendationBatchResult` contains:

- `recommendations` — all matched rule recommendations
- `primary` — highest priority score recommendation
- `calculation_timestamp`

## User Actions

| Action | Effect |
|--------|--------|
| Accept | Cache + memory updated, event published |
| Dismiss | Cache + memory updated, event published |
| Refresh | Cache invalidated, regenerated |

## Performance

Rule-based path targets under 200 ms excluding external LLM calls.
