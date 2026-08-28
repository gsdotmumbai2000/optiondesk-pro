"""Tests for MarketModeService's Live<->Simulator switch orchestration."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.brokers.shared.enums import BrokerCode
from app.config.models.app_config import BrokerConfig, MarketMode
from app.services.broker.market_mode_service import MarketModeService


@pytest.fixture
def broker_provider() -> MagicMock:
    provider = MagicMock()
    provider.manager.broker_code = BrokerCode.BREEZE.value

    def _switch(code: str) -> None:
        provider.manager.broker_code = code

    provider.manager.switch_to.side_effect = _switch
    return provider


@pytest.fixture
def market_data() -> MagicMock:
    market_data = MagicMock()
    market_data.dispatcher = MagicMock()
    return market_data


@pytest.fixture
def service(broker_provider: MagicMock, market_data: MagicMock, tmp_path: Path) -> MarketModeService:
    config = BrokerConfig(broker_code="BREEZE", market_mode=MarketMode.LIVE)
    return MarketModeService(broker_provider, market_data, config, tmp_path)


class TestApplySwitchesBrokerOnlyWhenEffectiveCodeChanges:
    def test_switching_to_simulator_calls_switch_to(
        self, service: MarketModeService, broker_provider: MagicMock
    ) -> None:
        service.apply(MarketMode.SIMULATOR)

        broker_provider.manager.switch_to.assert_called_once_with(BrokerCode.SIMULATOR.value)
        assert service.mode == MarketMode.SIMULATOR

    def test_switching_to_the_already_active_mode_is_a_noop(
        self, service: MarketModeService, broker_provider: MagicMock
    ) -> None:
        service.apply(MarketMode.LIVE)

        broker_provider.manager.switch_to.assert_not_called()

    def test_switching_back_to_live_calls_switch_to_with_live_broker_code(
        self, service: MarketModeService, broker_provider: MagicMock
    ) -> None:
        service.apply(MarketMode.SIMULATOR)
        broker_provider.manager.switch_to.reset_mock()

        service.apply(MarketMode.LIVE)

        broker_provider.manager.switch_to.assert_called_once_with("BREEZE")


class TestReplayEngineLifecycleIsSingleOwner:
    def test_no_recordings_available_switches_broker_without_raising(
        self, service: MarketModeService
    ) -> None:
        effective = service.apply(MarketMode.SIMULATOR)

        assert effective == BrokerCode.SIMULATOR.value

    def test_switching_away_from_simulator_stops_any_running_replay(
        self, service: MarketModeService
    ) -> None:
        service.apply(MarketMode.SIMULATOR)
        service._replay_engine = MagicMock()
        replay = service._replay_engine

        service.apply(MarketMode.LIVE)

        replay.stop.assert_called_once()
        assert service._replay_engine is None

    def test_stop_stops_a_running_replay_engine(self, service: MarketModeService) -> None:
        service._replay_engine = MagicMock()
        replay = service._replay_engine

        service.stop()

        replay.stop.assert_called_once()


class TestApplyPersistsConfiguration:
    def test_apply_saves_via_configuration_manager_when_provided(
        self, broker_provider: MagicMock, market_data: MagicMock, tmp_path: Path
    ) -> None:
        config = BrokerConfig(broker_code="BREEZE", market_mode=MarketMode.LIVE)
        configuration_manager = MagicMock()
        service = MarketModeService(
            broker_provider, market_data, config, tmp_path, configuration_manager=configuration_manager
        )

        service.apply(MarketMode.SIMULATOR)

        assert config.market_mode == MarketMode.SIMULATOR
        configuration_manager.save.assert_called_once()
