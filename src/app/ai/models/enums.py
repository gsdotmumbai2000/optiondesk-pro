"""AI recommendation domain enumerations."""

from enum import Enum


class AIModelVersion(str, Enum):
    """AI engine schema version."""

    V1 = "ai-recommendation-engine-v1"


class RecommendationCategory(str, Enum):
    """Recommendation categories."""

    NEW_STRATEGY = "NEW_STRATEGY"
    POSITION_ADJUSTMENT = "POSITION_ADJUSTMENT"
    TAKE_PROFIT = "TAKE_PROFIT"
    REDUCE_LOSS = "REDUCE_LOSS"
    ROLL_POSITION = "ROLL_POSITION"
    INCREASE_HEDGE = "INCREASE_HEDGE"
    REDUCE_MARGIN = "REDUCE_MARGIN"
    CAPITAL_OPTIMIZATION = "CAPITAL_OPTIMIZATION"
    RISK_REDUCTION = "RISK_REDUCTION"
    PORTFOLIO_DIVERSIFICATION = "PORTFOLIO_DIVERSIFICATION"


class RecommendationPriority(str, Enum):
    """Recommendation priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RuleCondition(str, Enum):
    """Configurable rule condition types."""

    DELTA_EXCEEDS = "DELTA_EXCEEDS"
    MARGIN_UTILIZATION_EXCEEDS = "MARGIN_UTILIZATION_EXCEEDS"
    POP_BELOW = "POP_BELOW"
    RISK_SCORE_EXCEEDS = "RISK_SCORE_EXCEEDS"
    LOSS_EXCEEDS = "LOSS_EXCEEDS"
    MARGIN_AVAILABLE_BELOW = "MARGIN_AVAILABLE_BELOW"
    HEALTH_SCORE_BELOW = "HEALTH_SCORE_BELOW"
    CUSTOM = "CUSTOM"


class EvidenceSource(str, Enum):
    """Traceable evidence source engines."""

    PORTFOLIO = "PORTFOLIO"
    RISK = "RISK"
    MARGIN = "MARGIN"
    PROBABILITY = "PROBABILITY"
    STRATEGY = "STRATEGY"
    OPTIMIZATION = "OPTIMIZATION"
    MONITOR = "MONITOR"
    MARKET = "MARKET"
    OPTION_CHAIN = "OPTION_CHAIN"
    VOLATILITY = "VOLATILITY"


class LLMProviderType(str, Enum):
    """Supported LLM provider types (framework)."""

    OPENAI = "OPENAI"
    AZURE_OPENAI = "AZURE_OPENAI"
    ANTHROPIC = "ANTHROPIC"
    AWS_BEDROCK = "AWS_BEDROCK"
    GOOGLE_GEMINI = "GOOGLE_GEMINI"
    LOCAL = "LOCAL"
    NULL = "NULL"


class PromptTemplateType(str, Enum):
    """Prompt template identifiers."""

    SYSTEM = "SYSTEM"
    MARKET_SUMMARY = "MARKET_SUMMARY"
    PORTFOLIO_SUMMARY = "PORTFOLIO_SUMMARY"
    STRATEGY_ANALYSIS = "STRATEGY_ANALYSIS"
    POSITION_REVIEW = "POSITION_REVIEW"
    RISK_REVIEW = "RISK_REVIEW"
    RECOMMENDATION = "RECOMMENDATION"
