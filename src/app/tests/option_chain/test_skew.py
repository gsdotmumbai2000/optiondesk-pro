"""Tests for atm_iv() and skew()."""

from datetime import datetime, timezone
from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.option_chain.analytics.skew import atm_iv, skew
from app.volatility.models.volatility_result import (
    ExpectedMove,
    HistoricalVolatility,
    VolatilityResult,
)


def _chain(*strikes: OptionStrikeSnapshot) -> OptionChainSnapshot:
    return OptionChainSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        spot_price=Decimal("24500"), atm_strike=Decimal("24500"), strikes=strikes,
    )


def _volatility(implied: Decimal) -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=implied, annualized_volatility=implied, realized_volatility=implied,
        historical_volatility=HistoricalVolatility(primary=implied),
        expected_move=ExpectedMove(to_expiry=Decimal("0")), iv_percentile=Decimal("50"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


class TestAtmIv:
    def test_returns_atm_call_iv_when_present(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24500"), call_iv=Decimal("0.18"), is_atm=True),
        )

        assert atm_iv(chain, _volatility(Decimal("0.20"))) == Decimal("0.18")

    def test_falls_back_to_atm_put_iv_when_no_call_iv(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24500"), put_iv=Decimal("0.22"), is_atm=True),
        )

        assert atm_iv(chain, _volatility(Decimal("0.20"))) == Decimal("0.22")

    def test_falls_back_to_volatility_result_when_no_atm_strike(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24400"), call_iv=Decimal("0.18")),
        )

        assert atm_iv(chain, _volatility(Decimal("0.20"))) == Decimal("0.20")

    def test_falls_back_to_volatility_result_when_atm_strike_has_no_iv(self) -> None:
        chain = _chain(OptionStrikeSnapshot(strike_price=Decimal("24500"), is_atm=True))

        assert atm_iv(chain, _volatility(Decimal("0.20"))) == Decimal("0.20")


class TestSkew:
    def test_matches_hand_computed_max_put_minus_min_call(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24300"), put_iv=Decimal("0.25")),
            OptionStrikeSnapshot(strike_price=Decimal("24400"), put_iv=Decimal("0.22")),
            OptionStrikeSnapshot(strike_price=Decimal("24600"), call_iv=Decimal("0.17")),
            OptionStrikeSnapshot(strike_price=Decimal("24700"), call_iv=Decimal("0.19")),
        )

        result = skew(chain, Decimal("0.20"))

        assert result == Decimal("0.25") - Decimal("0.17")

    def test_no_put_iv_data_returns_none(self) -> None:
        chain = _chain(OptionStrikeSnapshot(strike_price=Decimal("24600"), call_iv=Decimal("0.17")))

        assert skew(chain, Decimal("0.20")) is None

    def test_no_call_iv_data_returns_none(self) -> None:
        chain = _chain(OptionStrikeSnapshot(strike_price=Decimal("24300"), put_iv=Decimal("0.25")))

        assert skew(chain, Decimal("0.20")) is None

    def test_non_positive_atm_returns_none(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24300"), put_iv=Decimal("0.25")),
            OptionStrikeSnapshot(strike_price=Decimal("24600"), call_iv=Decimal("0.17")),
        )

        assert skew(chain, Decimal("0")) is None

    def test_zero_or_negative_iv_values_excluded_from_extrema(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24300"), put_iv=Decimal("0")),
            OptionStrikeSnapshot(strike_price=Decimal("24350"), put_iv=Decimal("0.25")),
            OptionStrikeSnapshot(strike_price=Decimal("24600"), call_iv=Decimal("0.17")),
        )

        assert skew(chain, Decimal("0.20")) == Decimal("0.25") - Decimal("0.17")
