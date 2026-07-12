"""UI test skeletons — do not execute in CI by default."""

import pytest

pytestmark = pytest.mark.skip(reason="UI skeleton — manual or future CI integration")


class TestMVVMInfrastructure:
    """MVVM base classes and commands."""

    def test_relay_command_execute(self) -> None:
        """RelayCommand should invoke execute callback."""
        pass

    def test_base_viewmodel_signals(self) -> None:
        """BaseViewModel should expose busy and status signals."""
        pass


class TestViewModels:
    """ViewModel layer communicates only with ApplicationProvider."""

    def test_trading_viewmodel_refresh(self) -> None:
        """TradingViewModel.refresh uses trading workspace service."""
        pass

    def test_market_viewmodel_background_worker(self) -> None:
        """MarketViewModel.refresh runs on background worker."""
        pass

    def test_portfolio_viewmodel_events(self) -> None:
        """PortfolioViewModel subscribes to portfolio_updated."""
        pass


class TestMainWindow:
    """Main window shell."""

    def test_workspace_tabs_count(self) -> None:
        """Main window should expose eight workspace tabs."""
        pass

    def test_navigation_syncs_tabs(self) -> None:
        """Navigation pane selection should switch workspace tab."""
        pass


class TestThemes:
    """Theme manager."""

    def test_cycle_themes(self) -> None:
        """ThemeManager cycles light, dark, high contrast."""
        pass
