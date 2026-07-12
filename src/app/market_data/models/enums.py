"""Market data domain enumerations."""

from enum import Enum


class InstrumentKind(str, Enum):
    """Market data instrument classification."""

    SPOT = "SPOT"
    INDEX = "INDEX"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    STOCK = "STOCK"


class SnapshotKind(str, Enum):
    """Snapshot classification."""

    CURRENT = "CURRENT"
    PREVIOUS = "PREVIOUS"
    DELTA = "DELTA"


class HistoryPeriod(str, Enum):
    """Historical data period."""

    INTRADAY = "INTRADAY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
