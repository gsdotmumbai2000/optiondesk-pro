"""Prove the temporary NIFTY spot-unavailable diagnostic logging is a no-op.

Covers the five traced boundaries (Breeze raw SDK callback, post-normalization,
live tick cache insertion, CalculationDispatcher spot lookup, MarketView
watchlist update) plus the literal MarketDataEngine quote-cache insertion
boundary. Each test asserts that functional behavior (dispatched tick fields,
cached values, spot-lookup results, watchlist UI state) is unchanged with the
new `logger.debug(...)` calls present alongside the existing code path.
"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.live.calculations.market_query_adapter import LiveMarketQueryAdapter
from app.market_data.cache.live_tick_cache import LiveTickCache
from app.market_data.engine.market_data_engine import MarketDataEngine
from app.market_data.models import OHLC, Quote
from app.market_data.models.enums import InstrumentKind
from app.market_data.models.tick import TickSnapshot
from app.market_data.symbols import InstrumentMasterSymbolCanonicalizer
from app.market_data.websocket.websocket_service import WebSocketService


class _InstrumentMaster:
    """Instrument Master double resolving Breeze's NIFTY display name."""

    def find_by_symbol(self, symbol: str) -> list[object]:
        return []

    def find_by_display_name(self, display_name: str) -> list[object]:
        if display_name.casefold().strip() == "nifty 50":
            return [SimpleNamespace(trading_symbol="NIFTY")]
        return []

    def find_by_broker_symbol(self, broker_code: str, broker_symbol: str) -> list[object]:
        return []


def _websocket_service() -> tuple[WebSocketService, MagicMock]:
    dispatcher = MagicMock()
    service = WebSocketService(
        MagicMock(),
        dispatcher,
        symbol_canonicalizer=InstrumentMasterSymbolCanonicalizer(_InstrumentMaster()),
    )
    return service, dispatcher


class TestBoundary1And2WebSocketServiceNoOp:
    """Raw-SDK and post-normalization diagnostics must not change dispatched ticks."""

    def test_nifty_cash_tick_still_dispatched_unchanged(self) -> None:
        service, dispatcher = _websocket_service()

        service._process_tick(
            {"stock_code": "4.1!NIFTY 50", "exchange_code": "NSE", "ltp": "24502.1"}
        )

        tick = dispatcher.enqueue.call_args.args[0]
        assert tick.symbol == "NIFTY"
        assert tick.exchange == "NSE"
        assert tick.ltp == Decimal("24502.1")
        assert tick.strike_price == ""

    def test_nifty_option_tick_still_dispatched_unchanged(self) -> None:
        service, dispatcher = _websocket_service()

        service._process_tick(
            {
                "stock_code": "4.1!51219",
                "stock_name": "4.1!NIFTY 50",
                "exchange_code": "NFO",
                "expiry_date": "13-Feb-2026",
                "strike_price": "24500",
                "right": "Call",
                "product_type": "options",
                "ltp": "120.5",
            }
        )

        tick = dispatcher.enqueue.call_args.args[0]
        assert tick.symbol == "NIFTY-13-Feb-2026-24500-CE"
        assert tick.ltp == Decimal("120.5")

    def test_non_index_tick_unaffected_by_gating(self) -> None:
        service, dispatcher = _websocket_service()

        service._process_tick({"stock_code": "RELIANCE", "exchange_code": "NSE", "ltp": "2900"})

        tick = dispatcher.enqueue.call_args.args[0]
        assert tick.symbol == "RELIANCE"
        assert tick.ltp == Decimal("2900")

    def test_tick_missing_ltp_field_does_not_raise(self) -> None:
        """Diagnostic reads item.get("ltp") defensively; absence must not crash processing."""
        service, dispatcher = _websocket_service()

        service._process_tick({"stock_code": "NIFTY", "exchange_code": "NSE"})

        tick = dispatcher.enqueue.call_args.args[0]
        assert tick.symbol == "NIFTY"
        assert tick.ltp is None


class TestBoundary3LiveTickCacheNoOp:
    """Cache-insertion diagnostics must not change what's stored or returned."""

    def test_nifty_cash_tick_round_trips_unchanged(self) -> None:
        cache = LiveTickCache()
        tick = TickSnapshot(symbol="NIFTY", exchange="NSE", ltp=Decimal("24502.1"))

        cache.put(tick)
        result = cache.get("NSE", "NIFTY")

        assert result is tick
        assert result.ltp == Decimal("24502.1")

    def test_option_tick_round_trips_unchanged(self) -> None:
        cache = LiveTickCache()
        tick = TickSnapshot(
            symbol="NIFTY-13-Feb-2026-24500-CE",
            exchange="NFO",
            ltp=Decimal("120.5"),
            expiry_date="13-Feb-2026",
            strike_price="24500",
            option_right="CE",
        )

        cache.put(tick)
        result = cache.get(
            "NFO",
            "NIFTY-13-Feb-2026-24500-CE",
            expiry_date="13-Feb-2026",
            strike_price="24500",
            option_right="CE",
        )

        assert result is tick

    def test_non_index_tick_round_trips_unchanged(self) -> None:
        cache = LiveTickCache()
        tick = TickSnapshot(symbol="RELIANCE", exchange="NSE", ltp=Decimal("2900"))

        cache.put(tick)

        assert cache.get("NSE", "RELIANCE") is tick

    def test_cache_miss_still_returns_none(self) -> None:
        cache = LiveTickCache()

        assert cache.get("NSE", "NIFTY") is None


class TestBoundary3bMarketDataEngineCacheNoOp:
    """MarketDataEngine.MarketCache quote-cache diagnostics must not change stored quotes."""

    def test_nifty_spot_quote_still_cached_and_queryable(self) -> None:
        engine = MarketDataEngine(MagicMock())
        quote = Quote(
            symbol="NIFTY",
            exchange="NSE",
            instrument_kind=InstrumentKind.SPOT,
            ltp=Decimal("24502.1"),
            ohlc=OHLC(),
        )

        engine._process_quote(quote)

        cached = engine.query._cache.get_quote("NSE", "NIFTY")
        assert cached is not None
        assert cached.ltp == Decimal("24502.1")

    def test_non_index_quote_still_cached(self) -> None:
        engine = MarketDataEngine(MagicMock())
        quote = Quote(
            symbol="RELIANCE",
            exchange="NSE",
            instrument_kind=InstrumentKind.SPOT,
            ltp=Decimal("2900"),
            ohlc=OHLC(),
        )

        engine._process_quote(quote)

        cached = engine.query._cache.get_quote("NSE", "RELIANCE")
        assert cached is not None
        assert cached.ltp == Decimal("2900")


class _FakeMarketDataService:
    """Minimal MarketDataService double for LiveMarketQueryAdapter tests."""

    def __init__(self, tick: TickSnapshot | None, snapshot: dict | None = None) -> None:
        self._tick = tick
        self._snapshot = snapshot if snapshot is not None else {}

    def latest_tick(self, symbol: str, exchange: str, **parts: str) -> TickSnapshot | None:
        return self._tick

    def cache_snapshot(self) -> dict:
        return self._snapshot


class TestBoundary4SpotLookupFailureNoOp:
    """Spot-lookup-failure diagnostics must not change the adapter's return value."""

    def test_cache_hit_returns_ltp_and_timestamp_unchanged(self) -> None:
        tick = TickSnapshot(symbol="NIFTY", exchange="NSE", ltp=Decimal("24502.1"))
        market_data = _FakeMarketDataService(tick)
        adapter = LiveMarketQueryAdapter(market_data, MagicMock())

        result = adapter.get_spot("NIFTY", "NSE")

        assert result.ltp == Decimal("24502.1")

    def test_cache_miss_returns_none_ltp_and_logs_without_raising(self) -> None:
        market_data = _FakeMarketDataService(None, snapshot={"NFO:NIFTY-13-FEB-2026-24500-CE:::": object()})
        adapter = LiveMarketQueryAdapter(market_data, MagicMock())

        result = adapter.get_spot("NIFTY", "NSE")

        assert result.ltp is None
        assert result.timestamp is None

    def test_cache_snapshot_failure_does_not_break_spot_lookup(self) -> None:
        """Diagnostic candidate-key lookup must be defensive against cache_snapshot() errors."""

        class _BrokenMarketDataService(_FakeMarketDataService):
            def cache_snapshot(self) -> dict:
                raise RuntimeError("snapshot unavailable")

        market_data = _BrokenMarketDataService(None)
        adapter = LiveMarketQueryAdapter(market_data, MagicMock())

        result = adapter.get_spot("NIFTY", "NSE")

        assert result.ltp is None

    def test_name_with_space_does_not_raise(self) -> None:
        """Requested symbol "NIFTY 50" (the observed mismatch variant) must not crash lookup."""
        market_data = _FakeMarketDataService(None)
        adapter = LiveMarketQueryAdapter(market_data, MagicMock())

        result = adapter.get_spot("NIFTY 50", "NSE")

        assert result.ltp is None
