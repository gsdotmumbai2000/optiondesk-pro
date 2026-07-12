"""Margin domain enumerations."""

from enum import Enum


class MarginModelVersion(str, Enum):
    """Margin engine schema version."""

    V1 = "margin-engine-v1"


class MarginSource(str, Enum):
    """Margin calculation source."""

    ESTIMATED = "estimated"
    BROKER = "broker"
    HYBRID = "hybrid"
