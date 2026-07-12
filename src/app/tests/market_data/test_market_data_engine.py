"""Market data engine tests."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.brokers.events import QuoteUpdatedEvent as BrokerQuoteUpdatedEvent
from app.brokers.shared.models import Quote as BrokerQuote
from app.events.event_bus import EventBus
from app.market_data.bootstrap import MarketDataProvider
from app.market_data.cache.market_cache import MarketCache
from app.market_data.cache.lru import LruTtlCache
from app.market_data.engine.market_data_engine import MarketDataEngine
from app.market_data.models import OHLC, Quote
from app.market_data.models.enums import InstrumentKind
from app.market_data.services.filter_service import MarketDataFilterService
from app.market_data.snapshots.snapshot_manager import SnapshotManager
from app.market_data.validation.validators import MarketDataValidator
from app.market_data.validation.exceptions import MarketDataValidationException
from app.tests.brokers.conftest import MockBreezeClient, broker_config, credential_manager


@pytest.fixture
def mock_broker(mock_client_factory: MagicMock, broker_config, credential_manager):
    """Create mock broker."""
    from app.brokers.bootstrap import BrokerProvider

    provider = BrokerProvider(
        broker_config,
        credential_manager,
        EventBus(),
        client_factory=mock_client_factory,
    )
    provider.manager.connect()
    return provider.broker_service


@pytest.fixture
def engine(mock_broker, tmp_path: Path) -> MarketDataEngine:
    """Create market data engine."""
    from app.market_data.repository.market_data_repository import MarketDataRepository

    bus = EventBus()
    bus.start()
    repo = MarketDataRepository(tmp_path / "market.db")
    engine = MarketDataEngine(mock_broker, bus, repo)
    engine.initialize()
    yield engine
    engine.shutdown()
    bus.stop()


def _sample_quote() -> Quote:
    return Quote(
        symbol="NIFTY",
        exchange="NFO",
        underlying="NIFTY",
        instrument_kind=InstrumentKind.FUTURE,
        ltp=Decimal("24500"),
        ohlc=OHLC(open=Decimal("24400"), high=Decimal("24600"), low=Decimal("24350"), close=Decimal("24500")),
        volume=1000,
        open_interest=5000,
        timestamp=datetime.now(timezone.utc),
    )


def test_ingest_and_query_quote(engine: MarketDataEngine) -> None:
    """Engine should cache and serve quotes."""
    quote = _sample_quote()
    engine.ingest_quote(quote)
    import time

    time.sleep(0.1)
    result = engine.query.get_latest("NIFTY", "NFO")
    assert result is not None
    assert result.ltp == Decimal("24500")


def test_broker_event_ingestion(engine: MarketDataEngine) -> None:
    """Engine should ingest broker quote events."""
    assert engine._event_bus is not None
    engine._event_bus.publish(
        BrokerQuoteUpdatedEvent(
            payload={
                "quote": BrokerQuote(
                    symbol="NIFTY",
                    exchange="NFO",
                    ltp=Decimal("24510"),
                    volume=100,
                ).model_dump()
            }
        )
    )
    import time

    time.sleep(0.15)
    latest = engine.query.get_latest("NIFTY", "NFO")
    assert latest is not None
    assert latest.ltp == Decimal("24510")


def test_query_option_chain(engine: MarketDataEngine) -> None:
    """Query service should fetch option chain."""
    chain = engine.query.get_option_chain("NIFTY", "NFO", "30-Jan-2026")
    assert chain.underlying == "NIFTY"
    assert len(chain.strikes) >= 1


def test_snapshot_manager() -> None:
    """Snapshot manager should capture and compute delta."""
    manager = SnapshotManager()
    quote = _sample_quote()
    manager.capture({"NFO:NIFTY": quote})
    quote2 = quote.model_copy(update={"ltp": Decimal("24550")})
    manager.capture({"NFO:NIFTY": quote2})
    delta = manager.delta()
    assert delta is not None
    assert "NFO:NIFTY" in delta.quotes


def test_validator_rejects_invalid_quote() -> None:
    """Validator should reject invalid quotes."""
    quote = _sample_quote()
    quote.ltp = Decimal("-1")
    with pytest.raises(MarketDataValidationException):
        MarketDataValidator().validate_quote(quote)


def test_filter_service() -> None:
    """Filter service should search cached quotes."""
    cache = MarketCache()
    cache.put_quote(_sample_quote())
    service = MarketDataFilterService(cache)
    assert len(service.find_by_symbol("NIFTY")) == 1
    assert len(service.filter_by_volume(service.find_by_symbol("NIFTY"), min_volume=500)) == 1


def test_lru_cache_ttl() -> None:
    """LRU cache should evict expired entries."""
    cache: LruTtlCache[str] = LruTtlCache(max_size=10, ttl_seconds=0)
    cache.put("a", "1")
    import time

    time.sleep(0.01)
    assert cache.get("a") is None


def test_provider_lifecycle(mock_broker, tmp_path: Path) -> None:
    """Provider should start and stop engine."""
    provider = MarketDataProvider(mock_broker, tmp_path, EventBus())
    provider.start()
    provider.stop()
