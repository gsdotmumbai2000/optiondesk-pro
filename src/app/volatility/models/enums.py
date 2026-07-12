"""Volatility domain enumerations."""

from enum import Enum


class VolatilityModelVersion(str, Enum):
    """Volatility engine model version identifier."""

    V1 = "volatility-v1"
