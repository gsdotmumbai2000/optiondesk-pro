"""Tests for BrokerHistoricalAdapter: the bridge from BrokerInterface.
get_historical_data() (broker-shared HistoricalBar, no symbol/exchange) into
the backtesting engine's HistoricalMarketData (domain HistoricalBar, with
symbol/exchange attached), used for on-demand real-history backtest runs.
"""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.application.services.broker_historical_adapter import BrokerHistoricalAdapter
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.shared.models.historical import HistoricalBar as BrokerHistoricalBar
from app.exceptions.broker_exception import BrokerException


class _FakeBroker:
    """Duck-typed BrokerInterface stand-in recording the exact request it
    receives."""

    def __init__(self, *, connected: bool = True) -> None:
        self._connected = connected
        self.received_request = None
        self.bars_response: list[BrokerHistoricalBar] = [
            BrokerHistoricalBar(
                timestamp=datetime(2026, 8, 1, tzinfo=timezone.utc),
                open=Decimal("24000"), high=Decimal("24200"),
                low=Decimal("23900"), close=Decimal("24100"),
                volume=1000, open_interest=None,
            ),
            BrokerHistoricalBar(
                timestamp=datetime(2026, 8, 2, tzinfo=timezone.utc),
                open=Decimal("24100"), high=Decimal("24300"),
                low=Decimal("24050"), close=Decimal("24250"),
                volume=1200, open_interest=None,
            ),
        ]
        self.error: Exception | None = None

    def is_connected(self) -> bool:
        return self._connected

    def get_historical_data(self, request):
        if self.error is not None:
            raise self.error
        self.received_request = request
        return self.bars_response


def _adapter(broker: _FakeBroker | None) -> BrokerHistoricalAdapter:
    provider = SimpleNamespace(broker=broker)
    return BrokerHistoricalAdapter(provider)


def _range() -> tuple[datetime, datetime]:
    return datetime(2026, 8, 1, tzinfo=timezone.utc), datetime(2026, 8, 16, tzinfo=timezone.utc)


class TestBrokerHistoricalAdapterGuardConditions:
    def test_no_broker_returns_none(self) -> None:
        adapter = _adapter(None)
        from_date, to_date = _range()

        assert adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date) is None

    def test_broker_not_connected_returns_none(self) -> None:
        adapter = _adapter(_FakeBroker(connected=False))
        from_date, to_date = _range()

        assert adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date) is None

    def test_broker_not_supported_returns_none_not_raises(self) -> None:
        broker = _FakeBroker()
        broker.error = BrokerNotSupportedException("Dhan broker is not yet implemented")
        adapter = _adapter(broker)
        from_date, to_date = _range()

        assert adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date) is None

    def test_broker_exception_returns_none_not_raises(self) -> None:
        broker = _FakeBroker()
        broker.error = BrokerException("API error")
        adapter = _adapter(broker)
        from_date, to_date = _range()

        assert adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date) is None

    def test_empty_bars_returns_none(self) -> None:
        broker = _FakeBroker()
        broker.bars_response = []
        adapter = _adapter(broker)
        from_date, to_date = _range()

        assert adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date) is None


class TestBrokerHistoricalAdapterSuccessfulLookup:
    def test_maps_bars_into_historical_market_data(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        from_date, to_date = _range()

        result = adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date)

        assert result is not None
        assert result.underlying == "NIFTY"
        assert result.exchange == "NFO"
        assert len(result.bars) == 2
        assert result.bars[0].symbol == "NIFTY"
        assert result.bars[0].exchange == "NFO"
        assert result.bars[0].close == Decimal("24100")
        assert result.bars[1].close == Decimal("24250")

    def test_sends_underlying_exchange_and_date_range_in_request(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        from_date, to_date = _range()

        adapter.get_historical_bars("BANKNIFTY", "NFO", from_date, to_date)

        assert broker.received_request.symbol == "BANKNIFTY"
        assert broker.received_request.exchange == "NFO"
        assert broker.received_request.from_date == from_date
        assert broker.received_request.to_date == to_date

    def test_requests_daily_interval_and_cash_product(self) -> None:
        """The underlying's own price history is what BacktestEngine prices
        trades off (see _maybe_execute) -- daily cash-segment candles, not
        an options-specific request."""
        broker = _FakeBroker()
        adapter = _adapter(broker)
        from_date, to_date = _range()

        adapter.get_historical_bars("NIFTY", "NFO", from_date, to_date)

        assert broker.received_request.interval.value == "1day"
        assert broker.received_request.product_type.value == "CASH"
