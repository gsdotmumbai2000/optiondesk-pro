"""Tests for BrokerManager.switch_to() runtime Live<->Simulator hot-swap."""

from unittest.mock import MagicMock

from app.brokers.bootstrap import BrokerProvider
from app.brokers.broker_manager.switchable_broker import SwitchableBroker
from app.brokers.shared.enums import BrokerCode
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


def test_broker_property_returns_a_stable_switchable_proxy(
    broker_provider: BrokerProvider,
) -> None:
    """The proxy identity must not change across a switch, since consumers
    (market data engine, subscription/websocket services) capture it once."""
    proxy = broker_provider.manager.broker
    assert isinstance(proxy, SwitchableBroker)

    broker_provider.manager.switch_to(BrokerCode.SIMULATOR.value)

    assert broker_provider.manager.broker is proxy


def test_switch_to_simulator_updates_delegate_and_active_code(
    broker_provider: BrokerProvider,
) -> None:
    proxy = broker_provider.manager.broker
    original_delegate = proxy.delegate

    broker_provider.manager.switch_to(BrokerCode.SIMULATOR.value)

    assert broker_provider.manager.broker_code == BrokerCode.SIMULATOR.value
    assert proxy.delegate is not original_delegate
    assert proxy.delegate.broker_code == BrokerCode.SIMULATOR
    assert proxy.delegate.is_connected() is True


def test_switch_back_to_live_reconnects_original_broker_code(
    broker_provider: BrokerProvider,
) -> None:
    broker_provider.manager.switch_to(BrokerCode.SIMULATOR.value)

    broker_provider.manager.switch_to("BREEZE")

    assert broker_provider.manager.broker_code == "BREEZE"
    assert broker_provider.manager.broker.delegate.broker_code == BrokerCode.BREEZE


def test_switch_to_same_active_code_is_a_noop(broker_provider: BrokerProvider) -> None:
    proxy = broker_provider.manager.broker
    delegate = proxy.delegate

    broker_provider.manager.switch_to("BREEZE")

    assert proxy.delegate is delegate


def test_switchable_broker_forwards_unknown_attributes_to_delegate() -> None:
    """WebSocketService relies on getattr(broker, "_websocket", None); the
    proxy must transparently forward attributes it doesn't itself define."""
    delegate = MagicMock()
    delegate._websocket = "the-real-websocket"
    proxy = SwitchableBroker(delegate)

    assert proxy._websocket == "the-real-websocket"


def test_initial_code_seeds_active_broker_code_without_touching_config() -> None:
    """The manager's active code may differ from BrokerConfig.broker_code
    (the fixed live-broker identity) when booting straight into simulator."""
    config = BrokerConfig(broker_code="BREEZE")
    provider = BrokerProvider(
        config,
        CredentialManager(),
        EventBus(),
        initial_broker_code=BrokerCode.SIMULATOR.value,
    )
    try:
        assert provider.manager.broker_code == BrokerCode.SIMULATOR.value
        assert config.broker_code == "BREEZE"
    finally:
        provider.stop()
