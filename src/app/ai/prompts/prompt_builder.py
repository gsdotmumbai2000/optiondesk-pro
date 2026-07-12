"""Prompt rendering service."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.enums import PromptTemplateType
from app.ai.models.prompts import PromptTemplate, RenderedPrompt
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.rules import RecommendationRule
from app.ai.prompts.templates import default_templates


class PromptBuilder:
    """Render prompt templates with engine context."""

    def __init__(self) -> None:
        """Initialize with default templates."""
        self._templates = {t.template_type: t for t in default_templates()}

    def render(
        self,
        template_type: PromptTemplateType,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
        rule: RecommendationRule | None = None,
    ) -> RenderedPrompt:
        """Render prompt with safe engine-derived placeholders."""
        template = self._templates[template_type]
        values = self._values(request, context, rule)
        content = template.content
        for key, value in values.items():
            content = content.replace(f"{{{key}}}", str(value))
        return RenderedPrompt(
            template_type=template_type,
            content=content,
            context_keys=tuple(values.keys()),
        )

    def get_template(self, template_type: PromptTemplateType) -> PromptTemplate | None:
        """Return template by type."""
        return self._templates.get(template_type)

    def _values(
        self,
        request: RecommendationAnalysisRequest,
        ctx: EngineContextSnapshot,
        rule: RecommendationRule | None,
    ) -> dict[str, str]:
        snap = request.market_snapshot
        strategy = request.strategy_evaluation
        monitor = request.position_monitor_result
        values = {
            "portfolio_value": str(ctx.portfolio_value),
            "unrealized_pnl": str(ctx.unrealized_pnl),
            "cash_balance": str(ctx.cash_balance),
            "risk_score": str(ctx.risk_score),
            "value_at_risk": str(ctx.value_at_risk),
            "net_delta": str(ctx.net_delta),
            "open_count": str(ctx.open_position_count),
            "health_score": str(ctx.health_score),
            "probability_of_profit": str(ctx.probability_of_profit),
            "snapshot_id": snap.snapshot_id if snap else "n/a",
            "captured_at": str(snap.captured_at) if snap else "n/a",
            "strategy_name": (
                strategy.strategy.name if strategy else "n/a"
            ),
        }
        if rule:
            values["category"] = rule.category.value
            values["suggested_action"] = rule.suggested_action
        if monitor:
            values["health_score"] = str(monitor.health_score)
        return values
