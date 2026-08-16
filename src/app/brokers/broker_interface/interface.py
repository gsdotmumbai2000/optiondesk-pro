"""Abstract broker interface."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.brokers.shared.enums import BrokerCode, ConnectionState
from app.brokers.shared.models import (BrokerHealth, BrokerProfile, Funds,
                                       HistoricalBar, HistoricalRequest,
                                       Holding, Margins, OptionChain,
                                       OptionChainRequest, Order,
                                       OrderModification, OrderRequest,
                                       Position, Quote, QuoteSubscription)


class BrokerInterface(ABC):
    """Generic broker contract used by all application modules."""

    @property
    @abstractmethod
    def broker_code(self) -> BrokerCode:
        """Return broker identifier."""

    @property
    @abstractmethod
    def connection_state(self) -> ConnectionState:
        """Return current connection state."""

    @abstractmethod
    def connect(self) -> None:
        """Establish broker connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from broker."""

    @abstractmethod
    def authenticate(self) -> None:
        """Authenticate with broker credentials."""

    @abstractmethod
    def refresh_session(self) -> None:
        """Refresh an active broker session."""

    @abstractmethod
    def logout(self) -> None:
        """Logout and invalidate session."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether broker is connected."""

    @abstractmethod
    def get_profile(self) -> BrokerProfile:
        """Return broker user profile."""

    @abstractmethod
    def get_funds(self) -> Funds:
        """Return available funds."""

    @abstractmethod
    def get_holdings(self) -> list[Holding]:
        """Return demat holdings."""

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Return open positions."""

    @abstractmethod
    def get_orders(
        self,
        exchange: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Order]:
        """Return order book."""

    @abstractmethod
    def place_order(self, request: OrderRequest) -> Order:
        """Place a new order."""

    @abstractmethod
    def modify_order(self, modification: OrderModification) -> Order:
        """Modify an existing order."""

    @abstractmethod
    def cancel_order(self, exchange: str, order_id: str) -> Order:
        """Cancel an order."""

    @abstractmethod
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
        """Return a live quote."""

    @abstractmethod
    def get_option_chain(self, request: OptionChainRequest) -> OptionChain:
        """Return normalized option chain."""

    @abstractmethod
    def get_historical_data(self, request: HistoricalRequest) -> list[HistoricalBar]:
        """Return historical OHLCV bars."""

    @abstractmethod
    def subscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Subscribe to live quotes."""

    @abstractmethod
    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Unsubscribe from live quotes."""

    @abstractmethod
    def subscribe_option_chain(self, request: OptionChainRequest) -> None:
        """Subscribe to option chain updates."""

    @abstractmethod
    def unsubscribe_option_chain(self, request: OptionChainRequest) -> None:
        """Unsubscribe from option chain updates."""

    @abstractmethod
    def download_instrument_master(self) -> list[dict[str, str]]:
        """Download broker instrument master."""

    @abstractmethod
    def calculate_margin(
        self, positions: list[OrderRequest], exchange_code: str
    ) -> Margins | None:
        """Return real pre-trade margin for a basket of positions, or None
        when the broker didn't actually compute one (e.g. no SPAN data
        available for the request)."""

    @abstractmethod
    def health(self) -> BrokerHealth:
        """Return broker health snapshot."""
