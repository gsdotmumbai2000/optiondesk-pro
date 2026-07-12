"""Payoff domain enumerations."""

from enum import Enum


class PayoffModelVersion(str, Enum):
    """Payoff engine model version identifier."""

    V1 = "payoff-v1"
