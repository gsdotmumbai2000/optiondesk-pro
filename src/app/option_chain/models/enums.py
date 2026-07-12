"""Option chain domain enumerations."""

from enum import Enum


class OptionChainModelVersion(str, Enum):
    """Option chain engine model version identifier."""

    V1 = "option-chain-v1"
