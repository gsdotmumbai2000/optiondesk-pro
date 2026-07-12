"""Option chain analysis result."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.option_chain.models.enums import OptionChainModelVersion


@dataclass(frozen=True, slots=True)
class OptionChainAnalysis:
    """Immutable option chain analytics output."""

    liquidity_score: Decimal
    put_call_ratio: Decimal
    atm_iv: Decimal
    total_call_oi: int
    total_put_oi: int
    skew: Decimal | None
    calculation_timestamp: datetime
    model_version: OptionChainModelVersion = OptionChainModelVersion.V1
