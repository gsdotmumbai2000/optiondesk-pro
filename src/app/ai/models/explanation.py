"""Explainability models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TradeOff:
    """Trade-off between risk and reward."""

    benefit: str
    risk: str


@dataclass(frozen=True, slots=True)
class Explanation:
    """Full explanation for a recommendation."""

    why: str
    supporting_data: str
    affected_metrics: tuple[str, ...]
    trade_offs: tuple[TradeOff, ...]
    potential_risks: tuple[str, ...]
    potential_rewards: tuple[str, ...]
