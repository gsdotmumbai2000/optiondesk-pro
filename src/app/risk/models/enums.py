"""Risk domain enumerations."""

from enum import Enum


class RiskModelVersion(str, Enum):
    """Risk engine schema version."""

    V1 = "risk-engine-v1"


class ConfidenceLevel(str, Enum):
    """VaR confidence levels."""

    P95 = "0.95"
    P99 = "0.99"


class VaRMethod(str, Enum):
    """Value-at-Risk calculation method."""

    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    VARIANCE_COVARIANCE = "variance_covariance"


class StressShockType(str, Enum):
    """Stress test shock classification."""

    PRICE = "price"
    IV = "iv"
    TIME = "time"
    RATE = "rate"
    COMBINED = "combined"
