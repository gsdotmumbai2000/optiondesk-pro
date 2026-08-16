"""Tests for liquidity_score(): a bucketed heuristic on total open
interest. Every bucket boundary is exercised explicitly."""

from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.option_chain.analytics.liquidity import liquidity_score


def _chain(*strikes: OptionStrikeSnapshot) -> OptionChainSnapshot:
    return OptionChainSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        spot_price=Decimal("24500"), atm_strike=Decimal("24500"), strikes=strikes,
    )


def _strike(call_oi: int | None, put_oi: int | None) -> OptionStrikeSnapshot:
    return OptionStrikeSnapshot(strike_price=Decimal("24500"), call_oi=call_oi, put_oi=put_oi)


class TestNoStrikes:
    def test_empty_chain_returns_50(self) -> None:
        assert liquidity_score(_chain()) == Decimal("50")


class TestZeroOpenInterest:
    def test_all_zero_oi_returns_40(self) -> None:
        assert liquidity_score(_chain(_strike(0, 0))) == Decimal("40")

    def test_none_oi_treated_as_zero_returns_40(self) -> None:
        assert liquidity_score(_chain(_strike(None, None))) == Decimal("40")


class TestBucketBoundaries:
    def test_just_above_zero_is_low_bucket_60(self) -> None:
        assert liquidity_score(_chain(_strike(1, 0))) == Decimal("60")

    def test_just_below_100k_is_low_bucket_60(self) -> None:
        assert liquidity_score(_chain(_strike(99_999, 0))) == Decimal("60")

    def test_exactly_100k_is_mid_bucket_75(self) -> None:
        assert liquidity_score(_chain(_strike(100_000, 0))) == Decimal("75")

    def test_just_below_1m_is_mid_bucket_75(self) -> None:
        assert liquidity_score(_chain(_strike(999_999, 0))) == Decimal("75")

    def test_exactly_1m_is_high_bucket_90(self) -> None:
        assert liquidity_score(_chain(_strike(1_000_000, 0))) == Decimal("90")

    def test_well_above_1m_is_high_bucket_90(self) -> None:
        assert liquidity_score(_chain(_strike(5_000_000, 0))) == Decimal("90")


class TestAggregatesAcrossStrikesAndSides:
    def test_sums_call_and_put_oi_across_all_strikes(self) -> None:
        chain = _chain(_strike(40_000, 30_000), _strike(20_000, 15_000))  # total 105,000

        assert liquidity_score(chain) == Decimal("75")
