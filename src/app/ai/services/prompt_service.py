"""Prompt application service."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.enums import PromptTemplateType
from app.ai.models.prompts import PromptTemplate, RenderedPrompt
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.rules import RecommendationRule
from app.ai.prompts.prompt_builder import PromptBuilder
from app.ai.providers.llm_provider import LLMProvider


class PromptService:
    """Render prompts and optionally invoke LLM provider."""

    def __init__(
        self,
        builder: PromptBuilder | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        """Initialize prompt service."""
        self._builder = builder or PromptBuilder()
        self._llm = llm_provider

    def render(
        self,
        template_type: PromptTemplateType,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
        rule: RecommendationRule | None = None,
    ) -> RenderedPrompt:
        """Render prompt template."""
        return self._builder.render(template_type, request, context, rule)

    def get_template(self, template_type: PromptTemplateType) -> PromptTemplate | None:
        """Return template by type."""
        return self._builder.get_template(template_type)

    def complete(self, prompt: RenderedPrompt) -> str:
        """Invoke LLM provider if available."""
        if self._llm is None or not self._llm.is_available():
            return ""
        return self._llm.complete(prompt).content
