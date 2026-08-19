"""Tests for TickCandleBuffer: aggregates a live tick stream into a bounded
rolling window of fixed-interval OHLC candles."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.ui.market.tick_candle_buffer import TickCandleBuffer

_T0 = datetime(2026, 8, 19, 9, 15, 0, tzinfo=timezone.utc)


class TestSingleBucketAggregation:
    def test_first_tick_opens_a_candle_with_ohlc_all_equal(self) -> None:
        buffer = TickCandleBuffer()

        buffer.add_tick(Decimal("100"), _T0)

        candle = buffer.candles[0]
        assert (candle.open, candle.high, candle.low, candle.close) == (
            Decimal("100"), Decimal("100"), Decimal("100"), Decimal("100"),
        )

    def test_ticks_within_the_same_interval_fold_into_one_candle(self) -> None:
        buffer = TickCandleBuffer(interval=timedelta(minutes=1))

        buffer.add_tick(Decimal("100"), _T0)
        buffer.add_tick(Decimal("105"), _T0 + timedelta(seconds=10))
        buffer.add_tick(Decimal("98"), _T0 + timedelta(seconds=20))
        buffer.add_tick(Decimal("102"), _T0 + timedelta(seconds=59))

        assert len(buffer.candles) == 1
        candle = buffer.candles[0]
        assert candle.open == Decimal("100")
        assert candle.high == Decimal("105")
        assert candle.low == Decimal("98")
        assert candle.close == Decimal("102")

    def test_tick_in_the_next_interval_opens_a_new_candle(self) -> None:
        buffer = TickCandleBuffer(interval=timedelta(minutes=1))

        buffer.add_tick(Decimal("100"), _T0)
        buffer.add_tick(Decimal("110"), _T0 + timedelta(minutes=1))

        assert len(buffer.candles) == 2
        assert buffer.candles[0].close == Decimal("100")
        assert buffer.candles[1].open == Decimal("110")

    def test_out_of_order_tick_older_than_current_candle_is_dropped(self) -> None:
        buffer = TickCandleBuffer(interval=timedelta(minutes=1))
        buffer.add_tick(Decimal("100"), _T0 + timedelta(minutes=5))

        buffer.add_tick(Decimal("999"), _T0)  # stale/replayed tick

        assert len(buffer.candles) == 1
        assert buffer.candles[0].close == Decimal("100")


class TestRollingWindowCap:
    def test_candle_count_never_exceeds_max_candles(self) -> None:
        buffer = TickCandleBuffer(interval=timedelta(minutes=1), max_candles=5)

        for i in range(20):
            buffer.add_tick(Decimal(i), _T0 + timedelta(minutes=i))

        assert len(buffer.candles) == 5

    def test_oldest_candles_are_dropped_first(self) -> None:
        buffer = TickCandleBuffer(interval=timedelta(minutes=1), max_candles=3)

        for i in range(5):
            buffer.add_tick(Decimal(i), _T0 + timedelta(minutes=i))

        opens = [c.open for c in buffer.candles]
        assert opens == [Decimal("2"), Decimal("3"), Decimal("4")]


class TestTickPayloadParsing:
    def test_valid_payload_is_added(self) -> None:
        buffer = TickCandleBuffer()

        added = buffer.add_tick_payload({"ltp": "24502.5", "timestamp": _T0.isoformat()})

        assert added is True
        assert len(buffer.candles) == 1
        assert buffer.candles[0].close == Decimal("24502.5")

    def test_missing_ltp_is_rejected_without_raising(self) -> None:
        buffer = TickCandleBuffer()

        added = buffer.add_tick_payload({"timestamp": _T0.isoformat()})

        assert added is False
        assert buffer.candles == ()

    def test_malformed_ltp_is_rejected_without_raising(self) -> None:
        buffer = TickCandleBuffer()

        added = buffer.add_tick_payload({"ltp": "not-a-number"})

        assert added is False
        assert buffer.candles == ()

    def test_missing_timestamp_falls_back_to_now_without_raising(self) -> None:
        buffer = TickCandleBuffer()

        added = buffer.add_tick_payload({"ltp": "100"})

        assert added is True
        assert len(buffer.candles) == 1


class TestClear:
    def test_clear_empties_the_buffer(self) -> None:
        buffer = TickCandleBuffer()
        buffer.add_tick(Decimal("100"), _T0)

        buffer.clear()

        assert buffer.candles == ()
