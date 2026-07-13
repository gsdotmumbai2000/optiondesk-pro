"""Live analytics enumerations."""

from enum import Enum


class RefreshMode(str, Enum):
    """Configurable live analytics refresh policy."""

    EVERY_TICK = "EveryTick"
    MS_250 = "250ms"
    MS_500 = "500ms"
    SEC_1 = "1s"
    SEC_5 = "5s"
    MANUAL = "Manual"


class ChainSide(str, Enum):
    """Option contract side."""

    CALL = "CALL"
    PUT = "PUT"
