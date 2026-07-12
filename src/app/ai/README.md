# Enterprise AI Recommendation Engine

The AI Recommendation Engine is a decision-support system for OptionDesk Pro. It analyzes engine outputs and generates traceable recommendations with mandatory explanations.

## Scope

- Analyze market, portfolio, strategies, positions, risk, margin, and probability
- Generate recommendations with explanations and supporting evidence
- Configurable rule engine for threshold-based suggestions
- Composite scoring (confidence, impact, risk, capital, liquidity, priority)
- LLM provider abstraction (no provider-specific APIs implemented)
- Prompt template framework
- Recommendation memory and cache

## Does NOT Calculate

- Pricing
- Greeks
- Probability
- Payoff
- Risk
- Margin
- Strategy mathematics

All quantitative values are consumed from frozen engines.

## Dependencies

- `PortfolioResult`, `RiskResult`, `MarginResult`, `ProbabilityResult`
- `StrategyEvaluation`, `OptimizationResult`
- `MonitorResult` (position monitor)
- `MarketSnapshot`, `OptionChainAnalysis`, `VolatilityResult`

## Module Layout

```
src/app/ai/
  engine/           RecommendationEngine orchestrator
  models/           Immutable domain models
  rules/            Configurable rule engine
  recommendations/  Generator and alternatives builder
  explainability/   Evidence and explanation builders
  scoring/          Composite scorer
  prompts/          Template framework
  providers/        LLM provider abstraction
  advisors/         Portfolio, risk, margin, strategy, market advisors
  memory/           Recommendation history framework
  analytics/        Context aggregator
  services/         AIRecommendation, Explanation, Prompt, RuleEngine
  cache/            RecommendationCache
  validation/       RecommendationValidator
  bootstrap.py      AIProvider
```

## Quick Start

```python
from app.ai import AIProvider, RecommendationAnalysisRequest

provider = AIProvider(event_bus=event_bus)

request = RecommendationAnalysisRequest(
    session_id="session-1",
    portfolio_result=portfolio_result,
    risk_result=risk_result,
    margin_result=margin_result,
    probability_result=probability_result,
    strategy_evaluation=strategy_evaluation,
    optimization_result=optimization_result,
    position_monitor_result=monitor_result,
    market_snapshot=market_snapshot,
)
batch = provider.service.generate(request)
primary = batch.primary
```

## Documentation

- [AI Architecture](../../docs/ai/ai-architecture.md)
- [Recommendation Flow](../../docs/ai/recommendation-flow.md)
- [Explainability Flow](../../docs/ai/explainability-flow.md)
- [Class Diagram](../../docs/ai/class-diagram.md)
- [Sequence Diagram](../../docs/ai/sequence-diagram.md)

## Out of Scope

Fine-tuned models, RAG, multi-agent AI, voice assistant, auto strategy builder, broker logic, UI.

## Performance

Target: rule-based recommendation generation under 200 ms (excluding external LLM latency).
