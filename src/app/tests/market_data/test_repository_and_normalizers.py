"""Repository and normalizer tests."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from app.brokers.shared.models import HistoricalBar as BrokerHistoricalBar
from app.brokers.shared.models import OptionChain as BrokerOptionChain
from app.brokers.shared.models import OptionChainLeg
from app.brokers.shared.models import Quote as BrokerQuote
from app.market_data.normalizer.chain_normalizer import normalize_option_chain
from app.market_data.normalizer.historical_normalizer import normalize_historical_bars
from app.market_data.normalizer.quote_normalizer import normalize_quote
from app.market_data.repository.market_data_repository import MarketDataRepository
from app.market_data.models import HistoricalBar, MarketStatistics


def test_quote_normalizer() -> None:
    """Normalizer should map broker quote."""
    quote = normalize_quote(
        BrokerQuote(symbol="NIFTY", exchange="NFO", ltp=Decimal("100"), volume=10)
    )
    assert quote.symbol == "NIFTY"
    assert quote.ltp == Decimal("100")


def test_chain_normalizer() -> None:
    """Normalizer should map option chain."""
    chain = normalize_option_chain(
        BrokerOptionChain(
            underlying="NIFTY",
            exchange="NFO",
            expiry_date="30-Jan-2026",
            rows=[
                OptionChainLeg(
                    strike_price=Decimal("24500"),
                    expiry_date="30-Jan-2026",
                    call_ltp=Decimal("100"),
                )
            ],
        )
    )
    assert chain.strikes[0].strike_price == Decimal("24500")


def test_historical_normalizer() -> None:
    """Normalizer should map historical bars."""
    bars = normalize_historical_bars(
        [
            BrokerHistoricalBar(
                timestamp=datetime.now(timezone.utc),
                open=Decimal("1"),
                high=Decimal("2"),
                low=Decimal("1"),
                close=Decimal("2"),
                volume=10,
            )
        ],
        symbol="NIFTY",
        exchange="NFO",
    )
    assert bars[0].symbol == "NIFTY"


def test_repository_round_trip(tmp_path: Path) -> None:
    """Repository should persist and load bars."""
    repo = MarketDataRepository(tmp_path / "market.db")
    repo.initialize()
    bar = HistoricalBar(
        symbol="NIFTY",
        exchange="NFO",
        timestamp=datetime.now(timezone.utc),
        open=Decimal("1"),
        high=Decimal("2"),
        low=Decimal("1"),
        close=Decimal("2"),
        volume=10,
    )
    repo.save_bars([bar])
    loaded = repo.load_bars("NIFTY", "NFO")
    assert len(loaded) == 1
    stats = MarketStatistics(symbol="NIFTY", exchange="NFO", total_volume=10)
    repo.save_statistics(stats)
    assert repo.load_statistics("NIFTY", "NFO") is not None
    repo.close()
