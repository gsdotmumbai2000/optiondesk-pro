"""Strike utility tests."""

from decimal import Decimal

from app.market.utils.strike_utils import (atm_strike, itm_strike,
                                           nearest_strike, next_strike,
                                           otm_strike, previous_strike,
                                           round_strike)


def test_round_and_nearest_strike() -> None:
    """Strikes should round to interval."""
    interval = Decimal("50")
    assert round_strike(Decimal("24520"), interval) == Decimal("24500")
    assert nearest_strike(Decimal("24535"), interval) == Decimal("24550")


def test_next_and_previous_strike() -> None:
    """Next and previous strikes should step by interval."""
    interval = Decimal("100")
    assert next_strike(Decimal("45000"), interval) == Decimal("45100")
    assert previous_strike(Decimal("45000"), interval) == Decimal("44900")


def test_atm_itm_otm_strikes() -> None:
    """Option strike helpers should respect right."""
    interval = Decimal("50")
    spot = Decimal("24500")
    assert atm_strike(spot, interval) == Decimal("24500")
    assert otm_strike(spot, interval, option_right="CE") == Decimal("24550")
    assert itm_strike(spot, interval, option_right="PE") == Decimal("24550")
