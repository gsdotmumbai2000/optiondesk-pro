"""Normalize Breeze option chain responses."""

from decimal import Decimal
from typing import Any

from app.brokers.breeze.utilities import to_decimal, to_int
from app.brokers.shared.models import OptionChain, OptionChainLeg


def normalize_option_chain(
    underlying: str,
    exchange: str,
    expiry_date: str,
    payload: Any,
    *,
    spot_price: Decimal | None = None,
    atm_strike: Decimal | None = None,
) -> OptionChain:
    """Convert Breeze option chain payload to domain model."""
    rows = payload if isinstance(payload, list) else []
    legs: list[OptionChainLeg] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        strike = to_decimal(row.get("strike_price")) or Decimal("0")
        right = str(row.get("right", "")).lower()
        leg = OptionChainLeg(
            strike_price=strike,
            expiry_date=expiry_date,
            call_symbol=str(row.get("stock_code", "")) if right == "call" else "",
            put_symbol=str(row.get("stock_code", "")) if right == "put" else "",
            call_ltp=to_decimal(row.get("ltp")) if right == "call" else None,
            put_ltp=to_decimal(row.get("ltp")) if right == "put" else None,
            call_oi=to_int(row.get("open_interest")) if right == "call" else None,
            put_oi=to_int(row.get("open_interest")) if right == "put" else None,
            call_volume=(
                to_int(row.get("total_quantity_traded")) if right == "call" else None
            ),
            put_volume=(
                to_int(row.get("total_quantity_traded")) if right == "put" else None
            ),
            call_iv=(
                to_decimal(row.get("implied_volatility")) if right == "call" else None
            ),
            put_iv=(
                to_decimal(row.get("implied_volatility")) if right == "put" else None
            ),
            is_atm=atm_strike == strike if atm_strike is not None else False,
        )
        legs.append(leg)
    calls = [leg for leg in legs if leg.call_symbol or leg.call_ltp is not None]
    puts = [leg for leg in legs if leg.put_symbol or leg.put_ltp is not None]
    return OptionChain(
        underlying=underlying,
        exchange=exchange,
        expiry_date=expiry_date,
        spot_price=spot_price,
        atm_strike=atm_strike,
        calls=calls,
        puts=puts,
        rows=legs,
    )
