"""Runtime diagnostics for the installed Breeze SDK."""

from __future__ import annotations

import traceback
from functools import wraps
from typing import Any

from app.logging.logging_manager import get_logger

logger = get_logger(__name__)

_PATCHED = False


def apply_breeze_sdk_diagnostics() -> None:
    """Instrument BreezeConnect.get_stock_token_value for subscription debugging."""
    global _PATCHED
    if _PATCHED:
        return

    from breeze_connect.breeze_connect import BreezeConnect

    original = BreezeConnect.get_stock_token_value

    @wraps(original)
    def instrumented_get_stock_token_value(
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
        _print_subscription_request(
            exchange_code=exchange_code,
            stock_code=stock_code,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            right=right,
            get_exchange_quotes=get_exchange_quotes,
            get_market_depth=get_market_depth,
        )
        _print_lookup_state(self, stock_code)

        try:
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
        except Exception:
            _print_sdk_exception()
            raise

        if isinstance(result, Exception):
            print(
                "\n========== BREEZE SDK INTERNAL EXCEPTION =========="
            )
            print(
                "SDK returned exception object: "
                f"{type(result).__name__}: {result}"
            )
            print("===================================================\n")
            raise result

        return result

    BreezeConnect.get_stock_token_value = instrumented_get_stock_token_value  # type: ignore[method-assign]
    _PATCHED = True
    logger.info("Breeze SDK get_stock_token_value diagnostics enabled")


def _print_subscription_request(
    *,
    exchange_code: str,
    stock_code: str,
    product_type: str,
    expiry_date: str,
    strike_price: str,
    right: str,
    get_exchange_quotes: bool,
    get_market_depth: bool,
) -> None:
    print("--------------------------------------------------")
    print("exchange_code")
    print(exchange_code)
    print("stock_code")
    print(stock_code)
    print("product_type")
    print(product_type)
    print("expiry_date")
    print(expiry_date)
    print("strike_date")
    print(strike_price)
    print("right")
    print(right)
    print("get_exchange_quotes")
    print(get_exchange_quotes)
    print("get_market_depth")
    print(get_market_depth)
    print("--------------------------------------------------")


def _print_lookup_state(client: Any, stock_code: str) -> None:
    stock_script_dict_list_exists = (
        hasattr(client, "stock_script_dict_list")
        and client.stock_script_dict_list is not None
    )
    print(f"stock_script_dict_list exists: {stock_script_dict_list_exists}")
    if not stock_script_dict_list_exists:
        return

    print(f"stock_script_dict_list length: {len(client.stock_script_dict_list)}")
    nse_dictionary = (
        client.stock_script_dict_list[1]
        if len(client.stock_script_dict_list) > 1
        else {}
    )
    print(f"NSE dictionary entries: {len(nse_dictionary)}")
    stock_code_exists = bool(stock_code) and stock_code in nse_dictionary
    print(f"requested stock_code exists in NSE dictionary: {stock_code_exists}")
    if stock_code and not stock_code_exists:
        print("first 50 available NSE keys:")
        print(list(nse_dictionary.keys())[:50])


def _print_sdk_exception() -> None:
    print("\n========== BREEZE SDK INTERNAL EXCEPTION ==========")
    traceback.print_exc()
    print("===================================================\n")
