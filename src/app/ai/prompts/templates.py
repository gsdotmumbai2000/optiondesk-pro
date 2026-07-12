"""Prompt template definitions."""

from app.ai.models.enums import PromptTemplateType
from app.ai.models.prompts import PromptTemplate


def default_templates() -> tuple[PromptTemplate, ...]:
    """Return default prompt templates."""
    return (
        PromptTemplate(
            PromptTemplateType.SYSTEM,
            "system",
            "You are an options trading decision-support assistant. "
            "Only use provided engine data. Never invent market data.",
        ),
        PromptTemplate(
            PromptTemplateType.MARKET_SUMMARY,
            "market_summary",
            "Market snapshot: {snapshot_id} captured at {captured_at}.",
        ),
        PromptTemplate(
            PromptTemplateType.PORTFOLIO_SUMMARY,
            "portfolio_summary",
            "Portfolio value: {portfolio_value}, PnL: {unrealized_pnl}, "
            "cash: {cash_balance}.",
        ),
        PromptTemplate(
            PromptTemplateType.STRATEGY_ANALYSIS,
            "strategy_analysis",
            "Strategy: {strategy_name}, POP: {probability_of_profit}.",
        ),
        PromptTemplate(
            PromptTemplateType.POSITION_REVIEW,
            "position_review",
            "Open positions: {open_count}, health: {health_score}.",
        ),
        PromptTemplate(
            PromptTemplateType.RISK_REVIEW,
            "risk_review",
            "Risk score: {risk_score}, VaR: {value_at_risk}, delta: {net_delta}.",
        ),
        PromptTemplate(
            PromptTemplateType.RECOMMENDATION,
            "recommendation",
            "Recommend action for {category}: {suggested_action}.",
        ),
    )
