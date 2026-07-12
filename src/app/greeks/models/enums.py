"""Greeks domain enumerations."""

from enum import Enum


class GreeksModelVersion(str, Enum):
    """Greeks engine model version identifier."""

    BLACK_SCHOLES_V1 = "black-scholes-greeks-v1"
