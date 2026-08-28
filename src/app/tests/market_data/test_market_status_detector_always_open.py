"""Market status detector always_open override tests."""

from unittest.mock import MagicMock

from app.brokers.shared.enums import BrokerCode
from app.market_data.models.live_status import LiveMarketStatus
from app.market_data.providers.market_status_detector import MarketStatusDetector
from app.market_data.websocket.enums import LiveConnectionStatus


def _connected_broker() -> MagicMock:
    broker = MagicMock()
    broker.is_connected.return_value = True
    return broker


def test_always_open_reports_open_regardless_of_wall_clock() -> None:
    """always_open should bypass NSE hours/weekday/holiday checks."""
    websocket = MagicMock()
    websocket.status = LiveConnectionStatus.CONNECTED
    detector = MarketStatusDetector(_connected_broker(), websocket, always_open=True)

    snapshot = detector.detect()

    assert snapshot.status == LiveMarketStatus.OPEN


def test_always_open_still_reports_connection_lost() -> None:
    """always_open should not mask a real connection loss."""
    broker = MagicMock()
    broker.is_connected.return_value = False
    websocket = MagicMock()
    websocket.status = LiveConnectionStatus.CONNECTED
    detector = MarketStatusDetector(broker, websocket, always_open=True)

    snapshot = detector.detect()

    assert snapshot.status == LiveMarketStatus.CONNECTION_LOST


def test_default_behavior_unaffected() -> None:
    """Without always_open, weekday/holiday/hours logic still applies (real broker path)."""
    websocket = MagicMock()
    websocket.status = LiveConnectionStatus.CONNECTED
    detector = MarketStatusDetector(_connected_broker(), websocket)

    snapshot = detector.detect()

    assert snapshot.status in {
        LiveMarketStatus.PRE_OPEN,
        LiveMarketStatus.OPEN,
        LiveMarketStatus.CLOSED,
        LiveMarketStatus.HOLIDAY,
    }


def test_simulator_broker_reports_simulated_not_open() -> None:
    """Replayed ticks must never be reported as a real "Open" market --
    that would mislead the status bar into claiming the real market is open
    when it's actually closed and the data is simulated."""
    broker = _connected_broker()
    broker.broker_code = BrokerCode.SIMULATOR
    websocket = MagicMock()
    websocket.status = LiveConnectionStatus.CONNECTED
    detector = MarketStatusDetector(broker, websocket)

    snapshot = detector.detect()

    assert snapshot.status == LiveMarketStatus.SIMULATED


def test_simulator_broker_still_reports_connection_lost() -> None:
    broker = MagicMock()
    broker.broker_code = BrokerCode.SIMULATOR
    broker.is_connected.return_value = False
    websocket = MagicMock()
    websocket.status = LiveConnectionStatus.CONNECTED
    detector = MarketStatusDetector(broker, websocket)

    snapshot = detector.detect()

    assert snapshot.status == LiveMarketStatus.CONNECTION_LOST
