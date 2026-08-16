"""Engine-level wiring test for OptionChainAnalyzer: proves liquidity,
put/call ratio, ATM IV, and skew are all computed from the same chain
snapshot and combined consistently."""

from datetime import datetime, timezone
from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.option_chain.engine.chain_analyzer import OptionChainAnalyzer
from app.option_chain.models.request import OptionChainAnalysisRequest
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


def _volatility() -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=Decimal("0.20"), annualized_volatility=Decimal("0.20"),
        realized_volatility=Decimal("0.20"), historical_volatility=HistoricalVolatility(primary=Decimal("0.20")),
        expected_move=ExpectedMove(to_expiry=Decimal("0")), iv_percentile=Decimal("50"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


class TestChainAnalyzerWiring:
    def test_combines_liquidity_ratio_atm_iv_and_skew_from_one_chain(self) -> None:
        chain = _chain(
            OptionStrikeSnapshot(
                strike_price=Decimal("24500"), is_atm=True,
                call_oi=200_000, put_oi=250_000, call_iv=Decimal("0.18"), put_iv=Decimal("0.19"),
            ),
            OptionStrikeSnapshot(
                strike_price=Decimal("24400"), call_oi=100_000, put_oi=90_000, put_iv=Decimal("0.24"),
            ),
            OptionStrikeSnapshot(
                strike_price=Decimal("24600"), call_oi=80_000, put_oi=70_000, call_iv=Decimal("0.16"),
            ),
        )
        request = OptionChainAnalysisRequest(
            context=None, option_chain=chain, greeks_result=None,
            volatility_result=_volatility(), market_snapshot=None,
        )

        result = OptionChainAnalyzer().analyze(request)

        assert result.total_call_oi == 200_000 + 100_000 + 80_000
        assert result.total_put_oi == 250_000 + 90_000 + 70_000
        assert result.put_call_ratio == Decimal(result.total_put_oi) / Decimal(result.total_call_oi)
        assert result.atm_iv == Decimal("0.18")  # ATM strike's own call_iv wins
        assert result.skew == Decimal("0.24") - Decimal("0.16")  # max put_iv - min call_iv
        assert result.liquidity_score == Decimal("75")  # total OI = 790,000 -> mid bucket

    def test_empty_chain_produces_defined_zero_state_not_crash(self) -> None:
        request = OptionChainAnalysisRequest(
            context=None, option_chain=_chain(), greeks_result=None,
            volatility_result=_volatility(), market_snapshot=None,
        )

        result = OptionChainAnalyzer().analyze(request)

        assert result.total_call_oi == 0
        assert result.total_put_oi == 0
        assert result.put_call_ratio == Decimal("1")
        assert result.atm_iv == Decimal("0.20")  # falls back to volatility_result
        assert result.skew is None
        assert result.liquidity_score == Decimal("50")
