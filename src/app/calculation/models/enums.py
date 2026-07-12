"""Calculation domain enumerations."""

from enum import Enum


class MarketSessionType(str, Enum):
    """Market session classification."""

    PRE_OPEN = "PRE_OPEN"
    REGULAR = "REGULAR"
    POST_CLOSE = "POST_CLOSE"
    CLOSED = "CLOSED"
    MUHURAT = "MUHURAT"


class ContextVersion(str, Enum):
    """Calculation context schema version."""

    V1 = "1.0.0"
