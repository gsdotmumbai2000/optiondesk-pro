"""Probability domain enumerations."""

from enum import Enum


class ProbabilityModelVersion(str, Enum):
    """Probability engine model version identifier."""

    V1 = "probability-v1"
