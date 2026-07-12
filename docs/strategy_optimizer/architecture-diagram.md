# Strategy Optimizer Architecture

```mermaid
flowchart TB
    subgraph Input
        A[OptimizationRequest]
        B[OptimizationPreferences]
        C[OptimizationConstraints]
    end

    subgraph Optimizer
        D[StrategyOptimizer]
        E[OptimizerEngine]
        F[CandidateGenerator]
        G[SearchAlgorithm]
        H[EvaluationPort]
        I[ConstraintChecker]
        J[CandidateFilter]
        K[Scorer]
        L[StrategyRanker]
    end

    subgraph FrozenEngines
        M[Strategy Engine]
        N[Pricing / Greeks / Volatility]
        O[Probability / Payoff]
        P[Risk / Margin]
    end

    A --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> M
    M --> N
    M --> O
    M --> P
    H --> I
    I --> J
    J --> K
    K --> L
    L --> D
```

## Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| Generators | Assemble leg combinations (no math) |
| Search | Select candidate subset (brute force default) |
| Evaluation Port | Delegate to Strategy Engine |
| Constraints | Filter using engine outputs |
| Scoring | Map engine scores (no formulas) |
| Ranking | Order by overall score |

## SOLID Principles

- **Single Responsibility:** Each package has one concern
- **Open/Closed:** Search algorithms extensible via `SearchAlgorithm` port
- **Dependency Inversion:** `EvaluationPort` injects Strategy Engine
