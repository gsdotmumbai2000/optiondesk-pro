"""Tests for the Black-Scholes implied volatility solver."""

import pytest

from app.pricing.black_scholes import formulas
from app.pricing.black_scholes.solver import implied_volatility
from app.pricing.models.enums import OptionType

_SPOT = 24500.0
_RATE = 0.07
_DIVIDEND = 0.0
_TIME_TO_EXPIRY = 7.0 / 365.0


def _price(strike: float, volatility: float, option_type: OptionType) -> float:
    d1_value = formulas.d1(_SPOT, strike, _RATE, _DIVIDEND, volatility, _TIME_TO_EXPIRY)
    d2_value = formulas.d2(d1_value, volatility, _TIME_TO_EXPIRY)
    if option_type == OptionType.CALL:
        return formulas.call_price(_SPOT, strike, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, d1_value, d2_value)
    return formulas.put_price(_SPOT, strike, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, d1_value, d2_value)


def test_round_trips_atm_call_price_to_known_volatility() -> None:
    known_vol = 0.15
    market_price = _price(24500.0, known_vol, OptionType.CALL)

    solved = implied_volatility(
        market_price, _SPOT, 24500.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.CALL,
    )

    assert solved == pytest.approx(known_vol, abs=1e-4)


def test_round_trips_atm_put_price_to_known_volatility() -> None:
    known_vol = 0.22
    market_price = _price(24500.0, known_vol, OptionType.PUT)

    solved = implied_volatility(
        market_price, _SPOT, 24500.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.PUT,
    )

    assert solved == pytest.approx(known_vol, abs=1e-4)


def test_round_trips_otm_call_price_to_known_volatility() -> None:
    known_vol = 0.35
    market_price = _price(25500.0, known_vol, OptionType.CALL)

    solved = implied_volatility(
        market_price, _SPOT, 25500.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.CALL,
    )

    assert solved == pytest.approx(known_vol, abs=1e-4)


def test_round_trips_itm_put_price_to_known_volatility() -> None:
    known_vol = 0.28
    market_price = _price(25500.0, known_vol, OptionType.PUT)

    solved = implied_volatility(
        market_price, _SPOT, 25500.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.PUT,
    )

    assert solved == pytest.approx(known_vol, abs=1e-4)


def test_returns_none_for_zero_time_to_expiry() -> None:
    solved = implied_volatility(100.0, _SPOT, 24500.0, _RATE, _DIVIDEND, 0.0, OptionType.CALL)

    assert solved is None


def test_returns_none_for_non_positive_market_price() -> None:
    solved = implied_volatility(0.0, _SPOT, 24500.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.CALL)

    assert solved is None


def test_returns_none_for_price_below_intrinsic_no_arbitrage_bound() -> None:
    """A deep-ITM call priced below its floor (S - K*disc) has no volatility
    that reproduces it -- the solver must not fabricate one."""
    unreachable_low_price = 1.0  # far below the deep-ITM floor
    solved = implied_volatility(
        unreachable_low_price, _SPOT, 20000.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.CALL,
    )

    assert solved is None


def test_returns_none_for_price_above_max_bound() -> None:
    unreachable_high_price = _SPOT * 10  # far above any BS price at 500% vol
    solved = implied_volatility(
        unreachable_high_price, _SPOT, 24500.0, _RATE, _DIVIDEND, _TIME_TO_EXPIRY, OptionType.CALL,
    )

    assert solved is None
