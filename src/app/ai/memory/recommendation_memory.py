"""Recommendation memory framework."""

from threading import RLock

from app.ai.models.memory import PinnedRecommendation, RecommendationMemoryState, UserPreferences
from app.ai.models.result import RecommendationResult


class RecommendationMemory:
    """In-memory recommendation history framework."""

    def __init__(self, *, recent_limit: int = 10, history_limit: int = 100) -> None:
        """Initialize memory store."""
        self._recent_limit = recent_limit
        self._history_limit = history_limit
        self._lock = RLock()
        self._recent: list[RecommendationResult] = []
        self._history: list[RecommendationResult] = []
        self._dismissed: set[str] = set()
        self._accepted: set[str] = set()
        self._pinned: list[PinnedRecommendation] = []
        self._preferences = UserPreferences()

    def record(self, results: tuple[RecommendationResult, ...]) -> None:
        """Record new recommendations."""
        with self._lock:
            for result in results:
                self._recent.insert(0, result)
                self._history.append(result)
            self._recent = self._recent[: self._recent_limit]
            self._history = self._history[-self._history_limit :]

    def dismiss(self, recommendation_id: str) -> None:
        """Dismiss recommendation."""
        with self._lock:
            self._dismissed.add(recommendation_id)

    def accept(self, recommendation_id: str) -> None:
        """Accept recommendation."""
        with self._lock:
            self._accepted.add(recommendation_id)

    def pin(self, pinned: PinnedRecommendation) -> None:
        """Pin recommendation."""
        with self._lock:
            self._pinned.append(pinned)

    def state(self) -> RecommendationMemoryState:
        """Return current memory state."""
        with self._lock:
            return RecommendationMemoryState(
                recent=tuple(self._recent),
                history=tuple(self._history),
                dismissed_ids=tuple(self._dismissed),
                accepted_ids=tuple(self._accepted),
                pinned=tuple(self._pinned),
                preferences=self._preferences,
            )

    def set_preferences(self, preferences: UserPreferences) -> None:
        """Update user preferences."""
        with self._lock:
            self._preferences = preferences
