"""Regression test: LiveMarketQueryAdapter.get_future() must not crash quote_key()."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.live.cache.option_cache import LiveOptionCache
from app.live.calculations.market_query_adapter import LiveMarketQueryAdapter
from app.market_data.cache.live_tick_cache import LiveTickCache
from app.market_data.models.future import FutureQuote
from app.market_data.models.tick import TickSnapshot
from app.market_data.services.market_cache_service import MarketCacheService
from app.market_data.services.market_data_service import MarketDataService
from app.market_data.symbols import InstrumentMasterSymbolCanonicalizer
from app.market_data.websocket.websocket_service import WebSocketService


class _FakeQueryEngine:
    """Stands in for engine.query's REST fallback (see
    MarketDataService.get_future()) -- returns whatever future quote the
    test configures, "no data" (ltp=None) by default, so a tick-cache miss
    with no broker data either still resolves to ltp=None rather than
    raising."""

    def __init__(self, future_quote: FutureQuote | None = None) -> None:
        self._future_quote = future_quote

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> FutureQuote:
        return self._future_quote or FutureQuote(
            symbol=symbol, exchange=exchange, underlying=symbol, expiry_date=expiry_date,
        )


def _adapter_with_cache(
    cache: MarketCacheService, *, rest_future_quote: FutureQuote | None = None
) -> LiveMarketQueryAdapter:
    engine = SimpleNamespace(query=_FakeQueryEngine(rest_future_quote))
    provider = SimpleNamespace(cache=cache, engine=engine)
    market_data = MarketDataService(provider)
    return LiveMarketQueryAdapter(market_data, LiveOptionCache())


def test_get_future_does_not_raise_on_cache_miss() -> None:
    adapter = _adapter_with_cache(MarketCacheService())

    result = adapter.get_future("NIFTY", "NFO", "18-Aug-2026")

    assert result.ltp is None


def test_get_future_falls_back_to_broker_rest_on_cache_miss() -> None:
    """No tick has streamed in yet, but the broker REST fetch has real
    data -- Evaluate/Optimize must use it rather than reporting
    unavailable, matching MarketDataService.get_option_chain()'s existing
    REST fallback."""
    rest_quote = FutureQuote(
        symbol="NIFTY", exchange="NFO", underlying="NIFTY", expiry_date="18-Aug-2026",
        ltp=25200,
    )
    adapter = _adapter_with_cache(MarketCacheService(), rest_future_quote=rest_quote)

    result = adapter.get_future("NIFTY", "NFO", "18-Aug-2026")

    assert result.ltp == 25200


def test_get_future_returns_cached_future_tick() -> None:
    cache = MarketCacheService()
    cache.put_tick(
        TickSnapshot(
            symbol="NIFTY",
            exchange="NFO",
            expiry_date="18-Aug-2026",
            product_type="FUTURES",
            ltp=25000,
        )
    )
    adapter = _adapter_with_cache(cache)

    result = adapter.get_future("NIFTY", "NFO", "18-Aug-2026")

    assert result.ltp == 25000


class _InstrumentMaster:
    """Resolves Breeze's NIFTY display name, same double used by
    test_websocket_option_tick.py for the equivalent options round trip."""

    def find_by_symbol(self, symbol: str) -> list[object]:
        return []

    def find_by_display_name(self, display_name: str) -> list[object]:
        if display_name.casefold().strip() == "nifty 50":
            return [SimpleNamespace(trading_symbol="NIFTY")]
        return []

    def find_by_broker_symbol(self, broker_code: str, broker_symbol: str) -> list[object]:
        return []


def test_realistic_future_tick_round_trips_from_raw_websocket_payload_to_get_future() -> None:
    """Full path: raw Breeze futures tick -> WebSocketService normalization
    -> LiveTickCache.put() -> MarketDataService.latest_tick() ->
    LiveMarketQueryAdapter.get_future(). Proves the cache-key match traced in
    Task 4 holds for a tick built through the real normalization code, not a
    hand-constructed TickSnapshot."""
    dispatcher = MagicMock()
    service = WebSocketService(
        MagicMock(),
        dispatcher,
        symbol_canonicalizer=InstrumentMasterSymbolCanonicalizer(_InstrumentMaster()),
    )

    # Raw Breeze futures payload: no 'right'/'strike_price' (unlike options),
    # product_type 'futures', exchange label mapping to NFO like option ticks.
    service._process_tick(
        {
            "stock_code": "4.1!45080",
            "stock_name": "4.1!NIFTY 50",
            "exchange_code": "NFO",
            "expiry_date": "18-Aug-2026",
            "product_type": "futures",
            "ltp": "25105.5",
        }
    )
    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.symbol == "NIFTY"
    assert tick.exchange == "NFO"
    assert tick.expiry_date == "18-Aug-2026"
    assert tick.strike_price == ""
    assert tick.option_right == ""

    live_cache = LiveTickCache()
    live_cache.put(tick)
    cache = MarketCacheService(live_cache=live_cache)
    adapter = _adapter_with_cache(cache)

    result = adapter.get_future("NIFTY", "NFO", "18-Aug-2026")

    assert result.ltp is not None
    assert str(result.ltp) == "25105.5"
