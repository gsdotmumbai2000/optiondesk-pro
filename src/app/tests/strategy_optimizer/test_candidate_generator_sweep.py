"""Tests for the widened CandidateGenerator: real strike/width sweeps
across single legs, vertical spreads, strangles, and iron condors, so
search algorithms (Simulated Annealing in particular) have an actual space
to search rather than a handful of fixed-ATM strategies.

CandidateGenerator.generate() only reads context.expiry/atm_strike/
strike_interval, so a duck-typed SimpleNamespace stands in for the full
CalculationContext -- no need to build the real factory chain.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.strategy.models.enums import StrategyType
from app.strategy_optimizer.generators.candidate_generator import CandidateGenerator


def _context(atm: str = "24400", step: str = "50") -> SimpleNamespace:
    return SimpleNamespace(
        expiry=date(2026, 8, 18),
        atm_strike=Decimal(atm),
        strike_interval=Decimal(step),
    )


class TestSingleLegSweep:
    def test_sweeps_multiple_strikes_not_just_atm(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        long_calls = [c for c in candidates if c.metadata.recognized_type == StrategyType.LONG_CALL]
        strikes = {c.legs[0].strike for c in long_calls}

        # 21 swept strikes (-10..+10 offsets) + 1 from the "Long Call"
        # builtin template, which also recognizes as LONG_CALL.
        assert len(long_calls) == 22
        assert len(strikes) == 21  # every offset produces a distinct strike
        assert Decimal("24400") in strikes  # ATM itself still included

    def test_all_four_single_leg_kinds_present(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        types = {c.metadata.recognized_type for c in candidates}
        assert StrategyType.LONG_CALL in types
        assert StrategyType.LONG_PUT in types
        assert StrategyType.SHORT_CALL in types
        assert StrategyType.SHORT_PUT in types

    def test_no_negative_or_zero_strikes_generated(self) -> None:
        """A far-out-of-the-money sweep near a low ATM must not produce a
        non-positive strike."""
        candidates = CandidateGenerator().generate(_context(atm="200", step="50"))

        for candidate in candidates:
            for leg in candidate.legs:
                assert leg.strike > 0


class TestVerticalSpreadSweep:
    def test_sweeps_multiple_widths(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        bull_calls = [c for c in candidates if c.metadata.recognized_type == StrategyType.BULL_CALL_SPREAD]

        # 8 swept widths + 1 from the "Bull Call Spread" builtin template.
        assert len(bull_calls) == 9
        widths = {c.legs[1].strike - c.legs[0].strike for c in bull_calls}
        assert widths >= {Decimal("50") * w for w in range(2, 17, 2)}  # upper-lower = 2*width*step


class TestStranglesAndCondors:
    def test_single_atm_straddle_unchanged(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        straddles = [c for c in candidates if c.metadata.recognized_type == StrategyType.LONG_STRADDLE]
        # 1 swept straddle (always ATM by definition) + 1 from the "Long
        # Straddle" builtin template (whose own fixed-strike leg is not
        # substituted with ATM, so only the swept one is guaranteed ATM).
        assert len(straddles) == 2
        atm_straddles = [
            s for s in straddles if s.legs[0].strike == s.legs[1].strike == Decimal("24400")
        ]
        assert len(atm_straddles) == 1

    def test_sweeps_multiple_strangle_widths(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        strangles = [c for c in candidates if c.metadata.recognized_type == StrategyType.LONG_STRANGLE]
        assert len(strangles) == 6  # widths 1..6

    def test_sweeps_multiple_condor_inner_outer_combinations(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        condors = [c for c in candidates if c.metadata.recognized_type == StrategyType.IRON_CONDOR]
        # 12 swept combinations (4 inner widths * 3 outer offsets) + 1 from
        # the "Iron Condor" builtin template.
        assert len(condors) == 13
        for condor in condors:
            put_buy, put_sell, call_sell, call_buy = (leg.strike for leg in condor.legs)
            assert put_buy < put_sell < call_sell < call_buy  # well-ordered wings


class TestOverallPoolSize:
    def test_pool_is_over_a_hundred_candidates(self) -> None:
        """The whole point of widening: give search algorithms an actual
        space, not the previous fixed 13-candidate pool."""
        candidates = CandidateGenerator().generate(_context())

        assert len(candidates) > 100

    def test_every_candidate_has_a_unique_strategy_id(self) -> None:
        candidates = CandidateGenerator().generate(_context())

        ids = {c.strategy_id for c in candidates}
        assert len(ids) == len(candidates)
