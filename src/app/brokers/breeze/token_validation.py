"""Production safety check for invalid Breeze stock_code token results.

Breeze's get_stock_token_value() looks up stock_code via
``dict.get(stock_code, False)``. When the code is absent, its own
subscribe_exception() only builds an Exception object without raising or
returning it, so execution falls through and stringifies the missing token
(Python False) directly into the channel string, e.g. "4.1!False" /
"4.2!False". subscribe_feeds()/unsubscribe_feeds() then treat that string as
a valid channel and report the call as successful.

This module patches BreezeConnect.get_stock_token_value to reject that result
before any caller can treat it as success. It is independent of
sdk_diagnostics.py (which is logging-only) so this protection holds even when
diagnostics are disabled or never imported.
"""

from __future__ import annotations

from functools import wraps
from typing import Any

_PATCHED = False


class BreezeInvalidStockCodeError(RuntimeError):
    """Raised when Breeze's own SDK resolves a stock_code to an invalid token."""


def _token_is_invalid(token: Any) -> bool:
    """True for a channel string whose token half is the stringified Python False."""
    return isinstance(token, str) and token.rsplit("!", maxsplit=1)[-1] == "False"


def apply_breeze_token_validation() -> None:
    """Patch BreezeConnect.get_stock_token_value to raise on invalid tokens.

    Protects subscribe_feeds() and unsubscribe_feeds() alike, since both call
    get_stock_token_value() internally before treating the SDK call as
    successful.
    """
    global _PATCHED
    if _PATCHED:
        return

    from breeze_connect.breeze_connect import BreezeConnect

    original = BreezeConnect.get_stock_token_value

    @wraps(original)
    def validated_get_stock_token_value(
        self: Any,
        exchange_code: str = "",
        stock_code: str = "",
        product_type: str = "",
        expiry_date: str = "",
        strike_price: str = "",
        right: str = "",
        get_exchange_quotes: bool = True,
        get_market_depth: bool = True,
    ) -> Any:
        result = original(
            self,
            exchange_code=exchange_code,
            stock_code=stock_code,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            right=right,
            get_exchange_quotes=get_exchange_quotes,
            get_market_depth=get_market_depth,
        )

        if isinstance(result, tuple) and any(_token_is_invalid(token) for token in result):
            raise BreezeInvalidStockCodeError(
                "Breeze returned an invalid token for "
                f"stock_code={stock_code!r} exchange_code={exchange_code!r}: "
                "stock_code was not found in Breeze's own scrip dictionary "
                f"(tokens={result!r})"
            )

        return result

    BreezeConnect.get_stock_token_value = validated_get_stock_token_value  # type: ignore[method-assign]
    _PATCHED = True
