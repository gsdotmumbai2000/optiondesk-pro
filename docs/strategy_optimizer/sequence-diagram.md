# Strategy Optimizer Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant StrategyOptimizer
    participant OptimizerValidator
    participant OptimizerEngine
    participant CandidateGenerator
    participant BruteForceSearch
    participant EvaluationPort
    participant StrategyEngine
    participant ConstraintChecker
    participant StrategyRanker
    participant OptimizationCache
    participant EventBus

    Client->>StrategyOptimizer: optimize(request)
    StrategyOptimizer->>OptimizerValidator: validate(request)
    OptimizerValidator-->>StrategyOptimizer: ok
    StrategyOptimizer->>EventBus: OptimizationStartedEvent
    StrategyOptimizer->>OptimizerEngine: optimize(request)
    OptimizerEngine->>CandidateGenerator: generate(context)
    CandidateGenerator-->>OptimizerEngine: candidates
    OptimizerEngine->>BruteForceSearch: search(candidates, request)
    BruteForceSearch-->>OptimizerEngine: search_space
    OptimizerEngine->>EvaluationPort: evaluate_batch(requests)
    EvaluationPort->>StrategyEngine: evaluate per candidate
    StrategyEngine-->>EvaluationPort: StrategyEvaluation
    EvaluationPort-->>OptimizerEngine: evaluations
    OptimizerEngine->>ConstraintChecker: passes each
    OptimizerEngine->>StrategyRanker: rank(candidates)
    StrategyRanker-->>OptimizerEngine: ranked
    OptimizerEngine-->>StrategyOptimizer: OptimizationResult
    StrategyOptimizer->>OptimizationCache: put(key, result)
    StrategyOptimizer->>EventBus: OptimizationCompletedEvent
    StrategyOptimizer->>EventBus: RecommendationGeneratedEvent
    StrategyOptimizer-->>Client: OptimizationResult
```

## Batch Evaluation

The optimizer builds `StrategyEvaluationRequest` for each candidate and calls `evaluate_batch` on the evaluation port. The Strategy Engine orchestrates all frozen quantitative engines per candidate — the optimizer never performs calculations directly.
