"""Backtesting domain enumerations."""

from enum import Enum


class BacktestModelVersion(str, Enum):
    """Backtest engine schema version."""

    V1 = "backtest-engine-v1"


class ReplayState(str, Enum):
    """Replay session state."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class OrderType(str, Enum):
    """Simulated order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "BUY"
    SELL = "SELL"


class ReplaySpeed(str, Enum):
    """Replay speed multiplier."""

    X1 = "1x"
    X2 = "2x"
    X5 = "5x"
    X10 = "10x"
    MAX = "MAX"
