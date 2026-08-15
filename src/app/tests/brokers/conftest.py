"""Broker test fixtures."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.brokers.bootstrap import BrokerProvider
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


class MockBreezeClient:
    """Mock Breeze SDK client."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def generate_session(self, api_secret: str, session_token: str) -> dict[str, Any]:
        return {"Success": {"session_token": session_token}}

    def get_customer_details(self, api_session: str = "") -> dict[str, Any]:
        return {
            "Success": {
                "idirect_userid": "USER1",
                "idirect_user_name": "Test User",
                "segments_allowed": {"Trading": "Y"},
                "exg_status": {"NFO": "O"},
            }
        }

    def get_funds(self) -> dict[str, Any]:
        return {"Success": {"total_bank_balance": "100000"}}

    def get_demat_holdings(self) -> dict[str, Any]:
        return {
            "Success": [
                {
                    "stock_code": "INFY",
                    "exchange_code": "NSE",
                    "quantity": "10",
                    "average_price": "1500",
                }
            ]
        }

    def get_portfolio_positions(self) -> dict[str, Any]:
        return {
            "Success": [
                {
                    "stock_code": "NIFTY",
                    "exchange_code": "NFO",
                    "product_type": "futures",
                    "quantity": "25",
                    "average_price": "24500",
                    "ltp": "24550",
                }
            ]
        }

    def get_order_list(
        self,
        exchange_code: str = "",
        from_date: str = "",
        to_date: str = "",
    ) -> dict[str, Any]:
        return {
            "Success": [
                {
                    "order_id": "ORD1",
                    "exchange_code": exchange_code,
                    "stock_code": "NIFTY",
                    "product_type": "futures",
                    "action": "buy",
                    "order_type": "limit",
                    "quantity": "25",
                    "status": "Executed",
                }
            ]
        }

    def place_order(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "Success": {
                "order_id": "ORD2",
                "exchange_code": kwargs.get("exchange_code", ""),
                "stock_code": kwargs.get("stock_code", ""),
                "product_type": kwargs.get("product", ""),
                "action": kwargs.get("action", ""),
                "order_type": kwargs.get("order_type", ""),
                "quantity": kwargs.get("quantity", ""),
                "status": "Requested",
            }
        }

    def modify_order(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "Success": {
                "order_id": kwargs.get("order_id", ""),
                "exchange_code": kwargs.get("exchange_code", ""),
                "stock_code": "NIFTY",
                "product_type": "futures",
                "action": "buy",
                "order_type": "limit",
                "quantity": kwargs.get("quantity", ""),
                "status": "Requested",
            }
        }

    def cancel_order(
        self, exchange_code: str = "", order_id: str = ""
    ) -> dict[str, Any]:
        return {
            "Success": {
                "order_id": order_id,
                "exchange_code": exchange_code,
                "stock_code": "NIFTY",
                "product_type": "futures",
                "action": "buy",
                "order_type": "limit",
                "quantity": "25",
                "status": "Cancelled",
            }
        }

    def get_quotes(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "Success": [
                {
                    "ltp": "24500",
                    "open": "24400",
                    "high": "24600",
                    "low": "24350",
                    "close": "24450",
                    "total_quantity_traded": "1000",
                    "open_interest": "5000",
                }
            ]
        }

    def get_option_chain_quotes(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "Success": [
                {
                    "strike_price": "24500",
                    "right": "call",
                    "ltp": "120",
                    "open_interest": "10000",
                    "stock_code": "NIFTY24JAN24500CE",
                }
            ]
        }

    def get_historical_data_v2(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "Success": [
                {
                    "datetime": "01-Jan-2026 09:15:00",
                    "open": "24400",
                    "high": "24500",
                    "low": "24350",
                    "close": "24480",
                    "volume": "1000",
                }
            ]
        }

    def get_stock_script_list(self) -> list[dict[str, str]]:
        return [{"stock_code": "NIFTY", "exchange_code": "NFO"}]

    def subscribe_feeds(self, **kwargs: Any) -> dict[str, Any]:
        return {"Success": {}}

    def unsubscribe_feeds(self, **kwargs: Any) -> dict[str, Any]:
        return {"Success": {}}

    def margin_calculator(self, lists: list[dict[str, Any]], exchange_code: str) -> dict[str, Any]:
        return {
            "Success": {
                "margin_calulation": lists,
                "non_span_margin_required": "5000",
                "order_value": "0",
                "order_margin": "15000",
                "trade_margin": None,
                "block_trade_margin": "0",
                "span_margin_required": "10000",
            },
            "Status": 200,
            "Error": None,
        }

    def ws_connect(self) -> None:
        return None

    def ws_disconnect(self) -> None:
        return None


@pytest.fixture
def broker_config() -> BrokerConfig:
    """Return broker configuration."""
    return BrokerConfig(
        broker_code="BREEZE",
        account_name="Default",
        websocket_enabled=True,
        auto_login=True,
    )


@pytest.fixture
def credential_manager() -> CredentialManager:
    """Return credential manager with test credentials."""
    manager = CredentialManager()
    manager.store_api_key("Default", "test-api-key")
    manager.store_api_secret("Default", "test-secret")
    manager.store_session_token("Default", "test-session")
    return manager


@pytest.fixture
def mock_client_factory() -> MagicMock:
    """Return injectable mock client factory."""
    return MagicMock(side_effect=lambda api_key: MockBreezeClient(api_key))


@pytest.fixture
def broker_provider(
    broker_config: BrokerConfig,
    credential_manager: CredentialManager,
    mock_client_factory: MagicMock,
) -> BrokerProvider:
    """Create broker provider with mocked Breeze client."""
    provider = BrokerProvider(
        broker_config,
        credential_manager,
        EventBus(),
        client_factory=mock_client_factory,
    )
    yield provider
    provider.stop()
