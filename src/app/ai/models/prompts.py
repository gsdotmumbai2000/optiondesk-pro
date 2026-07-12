"""Prompt template models."""

from dataclasses import dataclass

from app.ai.models.enums import PromptTemplateType


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Immutable prompt template."""

    template_type: PromptTemplateType
    name: str
    content: str
    version: str = "1.0"


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """Rendered prompt ready for LLM provider."""

    template_type: PromptTemplateType
    content: str
    context_keys: tuple[str, ...]
