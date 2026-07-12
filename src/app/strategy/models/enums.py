"""Strategy domain enumerations."""

from enum import Enum


class StrategyModelVersion(str, Enum):
    """Strategy engine schema version."""

    V1 = "strategy-engine-v1"


class LegKind(str, Enum):
    """Supported strategy leg kinds."""

    CALL_BUY = "CALL_BUY"
    CALL_SELL = "CALL_SELL"
    PUT_BUY = "PUT_BUY"
    PUT_SELL = "PUT_SELL"
    FUTURE_BUY = "FUTURE_BUY"
    FUTURE_SELL = "FUTURE_SELL"
    STOCK_BUY = "STOCK_BUY"
    STOCK_SELL = "STOCK_SELL"


class StrategyType(str, Enum):
    """Recognized strategy types (display/reporting only)."""

    LONG_CALL = "LONG_CALL"
    SHORT_CALL = "SHORT_CALL"
    LONG_PUT = "LONG_PUT"
    SHORT_PUT = "SHORT_PUT"
    COVERED_CALL = "COVERED_CALL"
    PROTECTIVE_PUT = "PROTECTIVE_PUT"
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"
    BULL_PUT_SPREAD = "BULL_PUT_SPREAD"
    BEAR_CALL_SPREAD = "BEAR_CALL_SPREAD"
    LONG_STRADDLE = "LONG_STRADDLE"
    SHORT_STRADDLE = "SHORT_STRADDLE"
    LONG_STRANGLE = "LONG_STRANGLE"
    SHORT_STRANGLE = "SHORT_STRANGLE"
    IRON_CONDOR = "IRON_CONDOR"
    IRON_BUTTERFLY = "IRON_BUTTERFLY"
    BUTTERFLY = "BUTTERFLY"
    BROKEN_WING_BUTTERFLY = "BROKEN_WING_BUTTERFLY"
    JADE_LIZARD = "JADE_LIZARD"
    RATIO_SPREAD = "RATIO_SPREAD"
    CALENDAR_SPREAD = "CALENDAR_SPREAD"
    DIAGONAL_SPREAD = "DIAGONAL_SPREAD"
    SYNTHETIC_FUTURE = "SYNTHETIC_FUTURE"
    COLLAR = "COLLAR"
    BOX_SPREAD = "BOX_SPREAD"
    CUSTOM = "CUSTOM"


class OptimizationGoal(str, Enum):
    """Future optimization goals (framework only)."""

    DELTA_NEUTRAL = "DELTA_NEUTRAL"
    THETA_POSITIVE = "THETA_POSITIVE"
    HIGH_POP = "HIGH_POP"
    LOW_MARGIN = "LOW_MARGIN"
    MAXIMUM_RR = "MAXIMUM_RR"
