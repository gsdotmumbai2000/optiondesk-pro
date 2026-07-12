"""Strategy recognition service."""

from app.strategy.models.enums import StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.recognition.recognizer import recognize_strategy


class StrategyRecognitionService:
    """Identify strategy types for display and reporting."""

    def recognize(self, legs: tuple[StrategyLeg, ...]) -> StrategyType:
        """Return recognized strategy type (does not affect calculations)."""
        return recognize_strategy(legs)
