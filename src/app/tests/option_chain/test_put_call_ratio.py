"""Tests for put_call_ratio()."""

from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.option_chain.analytics.put_call_ratio import put_call_ratio


def _chain(*strikes: OptionStrikeSnapshot) -> OptionChainSnapshot:
    return OptionChainSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        spot_price=Decimal("24500"), atm_strike=Decimal("24500"), strikes=strikes,
    )


class TestNormalRatio:
    def test_ratio_equals_put_oi_over_call_oi(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24500"), call_oi=40_000, put_oi=60_000),
        )

        ratio, call_oi, put_oi = put_call_ratio(chain)

        assert ratio == Decimal("60000") / Decimal("40000")
        assert call_oi == 40_000
        assert put_oi == 60_000

    def test_aggregates_across_multiple_strikes(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(strike_price=Decimal("24400"), call_oi=10_000, put_oi=5_000),
            OptionStrikeSnapshot(strike_price=Decimal("24600"), call_oi=20_000, put_oi=25_000),
        )

        ratio, call_oi, put_oi = put_call_ratio(chain)

        assert call_oi == 30_000
        assert put_oi == 30_000
        assert ratio == Decimal("1")


class TestZeroCallOi:
    def test_zero_call_oi_returns_ratio_one_but_real_put_oi(self) -> None:
        """Special-cased to avoid division by zero -- the ratio is a
        placeholder 1, but call_oi/put_oi still reflect the real totals."""
        chain = _chain(OptionStrikeSnapshot(strike_price=Decimal("24500"), call_oi=0, put_oi=15_000))

        ratio, call_oi, put_oi = put_call_ratio(chain)

        assert ratio == Decimal("1")
        assert call_oi == 0
        assert put_oi == 15_000

    def test_no_strikes_returns_ratio_one_with_zero_totals(self) -> None:
        ratio, call_oi, put_oi = put_call_ratio(_chain())

        assert ratio == Decimal("1")
        assert call_oi == 0
        assert put_oi == 0


class TestNoneOiTreatedAsZero:
    def test_none_call_oi_and_put_oi_do_not_crash(self) -> None:
        chain = _chain(OptionStrikeSnapshot(strike_price=Decimal("24500"), call_oi=None, put_oi=None))

        ratio, call_oi, put_oi = put_call_ratio(chain)

        assert ratio == Decimal("1")
        assert call_oi == 0
        assert put_oi == 0
