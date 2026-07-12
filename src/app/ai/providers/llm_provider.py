"""LLM provider abstraction (no provider-specific APIs)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.ai.models.enums import LLMProviderType
from app.ai.models.prompts import RenderedPrompt


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Normalized LLM response."""

    content: str
    model: str
    tokens_used: int = 0


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @property
    @abstractmethod
    def provider_type(self) -> LLMProviderType:
        """Return provider type identifier."""

    @abstractmethod
    def complete(self, prompt: RenderedPrompt) -> LLMResponse:
        """Generate completion from rendered prompt."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether provider is configured and available."""
