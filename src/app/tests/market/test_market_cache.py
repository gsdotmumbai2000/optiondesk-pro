"""Market cache and event tests."""

from app.events.application_events import ApplicationEvent
from app.market.bootstrap import MarketMasterProvider
from app.market.events import InstrumentLoadedEvent


def test_lazy_loading_publishes_event(market_provider: MarketMasterProvider) -> None:
    """Loading instruments should publish InstrumentLoadedEvent."""
    received: list[ApplicationEvent] = []
    market_provider.cache._event_bus.subscribe(  # noqa: SLF001
        InstrumentLoadedEvent,
        lambda event: received.append(event),
    )
    instruments = market_provider.cache.get_instruments()
    assert len(instruments) >= 5
    assert any(isinstance(event, InstrumentLoadedEvent) for event in received)


def test_cache_invalidate(market_provider: MarketMasterProvider) -> None:
    """Invalidating cache should require reload."""
    market_provider.cache.get_instruments()
    market_provider.cache.invalidate()
    assert market_provider.cache._instruments_loaded is False  # noqa: SLF001
