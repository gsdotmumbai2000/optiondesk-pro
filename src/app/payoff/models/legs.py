"""Payoff leg and portfolio models."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.pricing.models.enums import OptionType


@dataclass(frozen=True, slots=True)
class StrategyLeg:
    """Immutable payoff leg supporting options and synthetic positions."""

    strike: Decimal
    option_type: OptionType
    quantity: int
    premium: Decimal
    expiry: date
    multiplier: int = 1
    underlying: str = ""
    exchange: str = ""


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    """Immutable portfolio position composed of payoff legs."""

    legs: tuple[StrategyLeg, ...] = ()
