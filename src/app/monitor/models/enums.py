"""Monitor domain enumerations."""

from enum import Enum


class MonitorModelVersion(str, Enum):
    """Monitor engine schema version."""

    V1 = "monitor-engine-v1"


class AlertPriority(str, Enum):
    """Alert severity levels."""

    INFORMATION = "INFORMATION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertStatus(str, Enum):
    """Alert lifecycle status."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class RuleType(str, Enum):
    """Built-in alert rule types."""

    MAX_LOSS = "MAX_LOSS"
    MAX_PROFIT = "MAX_PROFIT"
    MAX_DELTA = "MAX_DELTA"
    MAX_GAMMA = "MAX_GAMMA"
    MAX_VEGA = "MAX_VEGA"
    MAX_THETA = "MAX_THETA"
    MAX_MARGIN = "MAX_MARGIN"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    TIME_TO_EXPIRY = "TIME_TO_EXPIRY"
    IV_SPIKE = "IV_SPIKE"
    IV_CRUSH = "IV_CRUSH"
    OI_SHIFT = "OI_SHIFT"
    PRICE_GAP = "PRICE_GAP"
    CUSTOM = "CUSTOM"


class TriggerType(str, Enum):
    """Alert trigger categories."""

    LOSS_THRESHOLD = "LOSS_THRESHOLD"
    PROFIT_TARGET = "PROFIT_TARGET"
    MARGIN_LIMIT = "MARGIN_LIMIT"
    DELTA_LIMIT = "DELTA_LIMIT"
    GAMMA_LIMIT = "GAMMA_LIMIT"
    THETA_DECAY = "THETA_DECAY"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"
    TIME_DECAY = "TIME_DECAY"
    EXPIRY_WARNING = "EXPIRY_WARNING"
    CUSTOM = "CUSTOM"


class MonitoringInterval(str, Enum):
    """Monitoring schedule intervals."""

    REAL_TIME = "REAL_TIME"
    EVERY_TICK = "EVERY_TICK"
    EVERY_SECOND = "EVERY_SECOND"
    EVERY_MINUTE = "EVERY_MINUTE"
    CUSTOM = "CUSTOM"


class PositionHealth(str, Enum):
    """Aggregated position health status."""

    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class RecommendationType(str, Enum):
    """Recommendation categories (framework only)."""

    REDUCE_POSITION = "REDUCE_POSITION"
    CLOSE_POSITION = "CLOSE_POSITION"
    ROLL_POSITION = "ROLL_POSITION"
    HEDGE_POSITION = "HEDGE_POSITION"
    TAKE_PROFIT = "TAKE_PROFIT"
    REDUCE_RISK = "REDUCE_RISK"
    INCREASE_CAPITAL = "INCREASE_CAPITAL"
