"""Pricing domain enumerations."""

from enum import Enum


class OptionType(str, Enum):
    """Supported option types."""

    CALL = "CALL"
    PUT = "PUT"


class ExerciseStyle(str, Enum):
    """Option exercise style."""

    EUROPEAN = "EUROPEAN"
    AMERICAN = "AMERICAN"


class ModelVersion(str, Enum):
    """Pricing model version identifier."""

    BLACK_SCHOLES_MERTON_V1 = "black-scholes-merton-v1"
