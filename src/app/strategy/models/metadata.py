"""Strategy metadata model."""

from dataclasses import dataclass
from datetime import datetime

from app.strategy.models.enums import StrategyModelVersion, StrategyType


@dataclass(frozen=True, slots=True)
class StrategyMetadata:
    """Immutable strategy metadata."""

    strategy_id: str
    name: str
    recognized_type: StrategyType
    description: str = ""
    tags: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: StrategyModelVersion = StrategyModelVersion.V1
