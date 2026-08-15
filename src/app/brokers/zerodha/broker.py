"""Placeholder Zerodha broker."""

from datetime import datetime
from typing import NoReturn

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


class ZerodhaBroker(BrokerInterface):
    """Future Zerodha implementation placeholder."""

    def __init__(self, config: BrokerConfig) -> None:
        """Initialize placeholder broker."""
        self._config = config

    @property
    def broker_code(self) -> BrokerCode:
        return BrokerCode.ZERODHA

    @property
    def connection_state(self) -> ConnectionState:
        return ConnectionState.DISCONNECTED

    def _unsupported(self) -> NoReturn:
        raise BrokerNotSupportedException("Zerodha broker is not yet implemented")

    def connect(self) -> None:
        self._unsupported()

    def disconnect(self) -> None:
        return None

    def authenticate(self) -> None:
        self._unsupported()

    def refresh_session(self) -> None:
        self._unsupported()

    def logout(self) -> None:
        return None

    def is_connected(self) -> bool:
        return False

    def get_profile(self) -> BrokerProfile:
        self._unsupported()

    def get_funds(self) -> Funds:
        self._unsupported()

    def get_holdings(self) -> list[Holding]:
        self._unsupported()

    def get_positions(self) -> list[Position]:
        self._unsupported()

    def get_orders(
        self,
        exchange: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Order]:
        self._unsupported()

    def place_order(self, request: OrderRequest) -> Order:
        self._unsupported()

    def modify_order(self, modification: OrderModification) -> Order:
        self._unsupported()

    def cancel_order(self, exchange: str, order_id: str) -> Order:
        self._unsupported()

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
        self._unsupported()

    def get_option_chain(self, request: OptionChainRequest) -> OptionChain:
        self._unsupported()

    def get_historical_data(self, request: HistoricalRequest) -> list[HistoricalBar]:
        self._unsupported()

    def subscribe_quotes(self, subscription: QuoteSubscription) -> None:
        self._unsupported()

    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        self._unsupported()

    def subscribe_option_chain(self, request: OptionChainRequest) -> None:
        self._unsupported()

    def unsubscribe_option_chain(self, request: OptionChainRequest) -> None:
        self._unsupported()

    def download_instrument_master(self) -> list[dict[str, str]]:
        self._unsupported()

    def calculate_margin(
        self, positions: list[OrderRequest], exchange_code: str
    ) -> Margins:
        self._unsupported()

    def health(self) -> BrokerHealth:
        return BrokerHealth(
            broker_code=BrokerCode.ZERODHA.value,
            connection_state=ConnectionState.DISCONNECTED,
            is_session_valid=False,
            message="Not implemented",
        )
