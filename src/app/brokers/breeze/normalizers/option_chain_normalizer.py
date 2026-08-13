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
    """Convert Breeze option chain payload to domain model.

    Breeze returns one row per (strike, right). Rows are grouped by strike
    so each strike produces exactly one ``OptionChainLeg`` carrying both the
    call and put side, rather than duplicate call-only/put-only rows.
    """
    rows = payload if isinstance(payload, list) else []
    legs_by_strike: dict[Decimal, OptionChainLeg] = {}
    resolved_spot = spot_price

    for row in rows:
        if not isinstance(row, dict):
            continue
        strike = to_decimal(row.get("strike_price")) or Decimal("0")
        right = str(row.get("right", "")).strip().lower()
        leg = legs_by_strike.get(strike)
        if leg is None:
            leg = OptionChainLeg(strike_price=strike, expiry_date=expiry_date)
            legs_by_strike[strike] = leg

        if right == "call":
            _apply_side(leg, row, is_call=True)
        elif right == "put":
            _apply_side(leg, row, is_call=False)

        if resolved_spot is None:
            resolved_spot = to_decimal(row.get("spot_price"))

    legs = sorted(legs_by_strike.values(), key=lambda item: item.strike_price)
    for leg in legs:
        leg.is_atm = atm_strike is not None and leg.strike_price == atm_strike

    calls = [leg for leg in legs if leg.call_symbol or leg.call_ltp is not None]
    puts = [leg for leg in legs if leg.put_symbol or leg.put_ltp is not None]
    return OptionChain(
        underlying=underlying,
        exchange=exchange,
        expiry_date=expiry_date,
        spot_price=resolved_spot,
        atm_strike=atm_strike,
        calls=calls,
        puts=puts,
        rows=legs,
    )


def _apply_side(leg: OptionChainLeg, row: dict, *, is_call: bool) -> None:
    """Populate one side (call or put) of a strike leg from a raw Breeze row.

    No implied volatility is synthesized here: Breeze's option-chain quotes
    payload does not provide it, so call_iv/put_iv stay None unless the
    broker payload happens to include an explicit ``implied_volatility``.
    """
    symbol = str(row.get("stock_code", ""))
    ltp = to_decimal(row.get("ltp"))
    bid = to_decimal(row.get("best_bid_price"))
    ask = to_decimal(row.get("best_offer_price"))
    oi = to_int(row.get("open_interest"))
    volume = to_int(row.get("total_quantity_traded"))
    iv = to_decimal(row.get("implied_volatility"))
    if is_call:
        leg.call_symbol = symbol
        leg.call_ltp = ltp
        leg.call_bid = bid
        leg.call_ask = ask
        leg.call_oi = oi
        leg.call_volume = volume
        leg.call_iv = iv
    else:
        leg.put_symbol = symbol
        leg.put_ltp = ltp
        leg.put_bid = bid
        leg.put_ask = ask
        leg.put_oi = oi
        leg.put_volume = volume
        leg.put_iv = iv
