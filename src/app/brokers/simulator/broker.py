"""Simulated broker: replays recorded NIFTY ticks instead of a live feed.

Selected via BrokerConfig.broker_code = "SIMULATOR". Account/order methods
return empty-but-valid results so unrelated UI widgets don't crash; trading
actions are explicitly unsupported since this simulates market data only
(the app already has app.paper_trading for order simulation). Tick delivery
happens out-of-band: ReplayEngine pushes TickSnapshot objects straight into
the live EventDispatcher, not through this broker's websocket shim.
"""

from datetime import datetime
from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.shared.enums import BrokerCode, ConnectionState
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.shared.models import (BrokerHealth, BrokerProfile, Funds,
                                       HistoricalBar, HistoricalRequest,
                                       Holding, Margins, OptionChain,
                                       OptionChainRequest, Order,
                                       OrderModification, OrderRequest,
                                       Position, Quote, QuoteSubscription)
from app.config.models.app_config import BrokerConfig
from app.brokers.simulator.recording_snapshot import RecordingSnapshot
from app.brokers.simulator.websocket import SimulatorWebSocket


def _find_latest_recording(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    candidates = sorted(directory.glob("nifty_*.jsonl"))
    return candidates[-1] if candidates else None


class SimulatorBroker(BrokerInterface):
    """Always-connected broker backed by replayed NIFTY tick recordings."""

    def __init__(self, config: BrokerConfig, data_directory: Path | None = None) -> None:
        """Initialize simulator broker."""
        self._config = config
        self._connected = False
        self._websocket = SimulatorWebSocket()
        recording_path = (
            _find_latest_recording(data_directory / "simulator" / "recordings")
            if data_directory is not None
            else None
        )
        self._snapshot = RecordingSnapshot(recording_path)

    @property
    def broker_code(self) -> BrokerCode:
        return BrokerCode.SIMULATOR

    @property
    def connection_state(self) -> ConnectionState:
        return ConnectionState.CONNECTED if self._connected else ConnectionState.DISCONNECTED

    def connect(self) -> None:
        """Mark simulator connected; no real network/credentials involved."""
        self._connected = True
        self._websocket.connect()

    def disconnect(self) -> None:
        self._connected = False
        self._websocket.disconnect()

    def authenticate(self) -> None:
        self.connect()

    def refresh_session(self) -> None:
        return None

    def logout(self) -> None:
        self.disconnect()

    def is_connected(self) -> bool:
        return self._connected

    def get_profile(self) -> BrokerProfile:
        return BrokerProfile(broker_code=BrokerCode.SIMULATOR.value, user_name="Simulator")

    def get_funds(self) -> Funds:
        return Funds()

    def get_holdings(self) -> list[Holding]:
        return []

    def get_positions(self) -> list[Position]:
        return []

    def get_orders(
        self,
        exchange: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Order]:
        return []

    def place_order(self, request: OrderRequest) -> Order:
        raise BrokerNotSupportedException(
            "Order placement is not available in simulator mode"
        )

    def modify_order(self, modification: OrderModification) -> Order:
        raise BrokerNotSupportedException(
            "Order modification is not available in simulator mode"
        )

    def cancel_order(self, exchange: str, order_id: str) -> Order:
        raise BrokerNotSupportedException(
            "Order cancellation is not available in simulator mode"
        )

    def get_quotes(
        self,
        symbol: str,
        exchange: str,
        *,
        expiry_date: str = "",
        product_type: str = "",
        option_right: str = "",
        strike_price: str = "",
    ) -> Quote:
        return self._snapshot.quote(symbol, exchange)

    def get_option_chain(self, request: OptionChainRequest) -> OptionChain:
        return self._snapshot.option_chain(request)

    def get_historical_data(self, request: HistoricalRequest) -> list[HistoricalBar]:
        return []

    def subscribe_quotes(self, subscription: QuoteSubscription) -> None:
        self._websocket.subscribe_quotes(subscription)

    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        self._websocket.unsubscribe_quotes(subscription)

    def subscribe_option_chain(self, request: OptionChainRequest) -> None:
        self._websocket.subscribe_option_chain(request)

    def unsubscribe_option_chain(self, request: OptionChainRequest) -> None:
        self._websocket.unsubscribe_option_chain(request)

    def download_instrument_master(self) -> list[dict[str, str]]:
        return []

    def calculate_margin(
        self, positions: list[OrderRequest], exchange_code: str
    ) -> Margins | None:
        return None

    def health(self) -> BrokerHealth:
        return BrokerHealth(
            broker_code=BrokerCode.SIMULATOR.value,
            connection_state=self.connection_state,
            is_session_valid=self._connected,
            websocket_connected=self._websocket.is_connected,
            message="simulated" if self._connected else "disconnected",
        )
