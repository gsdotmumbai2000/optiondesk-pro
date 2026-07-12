"""Memory domain models."""

from dataclasses import dataclass, field
from datetime import datetime

from app.ai.models.result import RecommendationResult


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """User preference framework (no persistence)."""

    risk_tolerance: str = "moderate"
    preferred_categories: tuple[str, ...] = ()
    dismissed_categories: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PinnedRecommendation:
    """Pinned recommendation reference."""

    recommendation_id: str
    pinned_at: datetime
    note: str = ""


@dataclass(frozen=True, slots=True)
class RecommendationMemoryState:
    """In-memory recommendation history framework."""

    recent: tuple[RecommendationResult, ...]
    history: tuple[RecommendationResult, ...]
    dismissed_ids: tuple[str, ...] = ()
    accepted_ids: tuple[str, ...] = ()
    pinned: tuple[PinnedRecommendation, ...] = ()
    preferences: UserPreferences = field(default_factory=UserPreferences)
