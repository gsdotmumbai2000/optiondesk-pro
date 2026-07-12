"""Null LLM provider (rule-based only, no external API)."""

from app.ai.models.enums import LLMProviderType
from app.ai.models.prompts import RenderedPrompt
from app.ai.providers.llm_provider import LLMProvider, LLMResponse


class NullLLMProvider(LLMProvider):
    """Default provider that does not call external LLMs."""

    @property
    def provider_type(self) -> LLMProviderType:
        """Return null provider type."""
        return LLMProviderType.NULL

    def complete(self, prompt: RenderedPrompt) -> LLMResponse:
        """Return empty completion (rules drive recommendations)."""
        return LLMResponse(content="", model="null", tokens_used=0)

    def is_available(self) -> bool:
        """Null provider is always available."""
        return True
