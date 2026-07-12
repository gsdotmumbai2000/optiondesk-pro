"""Quant domain enumerations."""

from enum import Enum


class QuantModelVersion(str, Enum):
    """Quant integration layer version identifier."""

    V1 = "quant-v1"
