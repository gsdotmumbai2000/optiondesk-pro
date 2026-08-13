"""Normalize Breeze quote responses."""

from datetime import datetime, timezone
from typing import Any

from app.brokers.breeze.utilities import to_decimal, to_int
from app.brokers.shared.models import Quote, QuoteDepthLevel


def normalize_quote(
    symbol: str,
    exchange: str,
    payload: Any,
) -> Quote:
    """Convert Breeze quote payload to domain Quote."""
    data = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(data, dict):
        data = {}
    return Quote(
        symbol=symbol,
        exchange=exchange,
        ltp=to_decimal(data.get("ltp") or data.get("last_price") or data.get("last") or data.get("last_trade_price")),
        open=to_decimal(data.get("open")),
        high=to_decimal(data.get("high")),
        low=to_decimal(data.get("low")),
        close=to_decimal(data.get("close") or data.get("previous_close")),
        bid=to_decimal(data.get("best_bid_price") or data.get("bPrice") or data.get("bid_price")),
        ask=to_decimal(data.get("best_offer_price") or data.get("sPrice") or data.get("offer_price")),
        volume=to_int(data.get("total_quantity_traded") or data.get("ttq") or data.get("total_traded_volume")),
        open_interest=to_int(
            data.get("open_interest") or data.get("open_interest_value") or data.get("OI")
        ),
        change=to_decimal(data.get("change") or data.get("absolute_change") or data.get("ltp_percent_change")),
        change_percent=to_decimal(data.get("percentage_change")),
        timestamp=datetime.now(timezone.utc),
        bid_depth=_depth(data.get("bids")),
        ask_depth=_depth(data.get("offers")),
    )


def _depth(levels: Any) -> list[QuoteDepthLevel]:
    """Normalize depth levels."""
    if not isinstance(levels, list):
        return []
    result: list[QuoteDepthLevel] = []
    for level in levels:
        if not isinstance(level, dict):
            continue
        price = to_decimal(level.get("price"))
        qty = to_int(level.get("quantity"))
        if price is None or qty is None:
            continue
        result.append(
            QuoteDepthLevel(
                price=price,
                quantity=qty,
                orders=to_int(level.get("orders")) or 0,
            )
        )
    return result
