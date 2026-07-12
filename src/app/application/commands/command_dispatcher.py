"""Command dispatcher."""

from typing import Any

from app.application.exceptions import InvalidApplicationInput
from app.application.models.commands import ApplicationCommand
from app.application.models.enums import CommandType
from app.application.services.ai_workspace_service import AIWorkspaceService
from app.application.services.backtesting_workspace_service import BacktestingWorkspaceService
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.application.services.portfolio_workspace_service import PortfolioWorkspaceService
from app.application.services.strategy_workspace_service import StrategyWorkspaceService
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.validation.application_validator import ApplicationValidator


class CommandDispatcher:
    """Dispatch application commands to workspace services."""

    def __init__(
        self,
        validator: ApplicationValidator,
        trading: TradingWorkspaceService,
        strategy: StrategyWorkspaceService,
        portfolio: PortfolioWorkspaceService,
        backtesting: BacktestingWorkspaceService,
        market: MarketWorkspaceService,
        ai: AIWorkspaceService,
    ) -> None:
        """Initialize dispatcher."""
        self._validator = validator
        self._trading = trading
        self._strategy = strategy
        self._portfolio = portfolio
        self._backtesting = backtesting
        self._market = market
        self._ai = ai

    def dispatch(self, command: ApplicationCommand) -> Any:
        """Dispatch command to appropriate handler."""
        self._validator.validate_command(command)
        handlers = {
            CommandType.OPEN_STRATEGY: self._open_strategy,
            CommandType.SAVE_STRATEGY: self._save_strategy,
            CommandType.RUN_OPTIMIZATION: self._run_optimization,
            CommandType.RUN_BACKTEST: self._run_backtest,
            CommandType.REFRESH_MARKET: self._refresh_market,
            CommandType.GENERATE_REPORT: self._generate_report,
            CommandType.LOAD_PORTFOLIO: self._load_portfolio,
            CommandType.REFRESH_PORTFOLIO: self._refresh_portfolio,
            CommandType.GENERATE_RECOMMENDATION: self._generate_recommendation,
        }
        handler = handlers.get(command.command_type)
        if handler is None:
            raise InvalidApplicationInput(f"unsupported command: {command.command_type}")
        return handler(command)

    def _open_strategy(self, command: ApplicationCommand):
        return self._strategy.load_strategy(
            command.session_id,
            command.payload["strategy_id"],
        )

    def _save_strategy(self, command: ApplicationCommand):
        strategy = command.payload.get("strategy")
        if strategy is None:
            raise InvalidApplicationInput("save strategy requires strategy payload")
        return self._trading.save_strategy(command.session_id, strategy)

    def _run_optimization(self, command: ApplicationCommand):
        request = command.payload.get("request")
        if request is None:
            raise InvalidApplicationInput("optimization requires request payload")
        return self._trading.optimize_strategy(command.session_id, request)

    def _run_backtest(self, command: ApplicationCommand):
        request = command.payload.get("request")
        if request is None:
            raise InvalidApplicationInput("backtest requires request payload")
        return self._backtesting.run_backtest(command.session_id, request)

    def _refresh_market(self, command: ApplicationCommand):
        return self._market.refresh_market(command.session_id)

    def _generate_report(self, command: ApplicationCommand):
        result = command.payload.get("portfolio_result")
        if result is None:
            raise InvalidApplicationInput("report requires portfolio_result")
        return self._portfolio.generate_report(command.session_id, result)

    def _load_portfolio(self, command: ApplicationCommand):
        return self._portfolio.load_portfolio(
            command.session_id,
            command.payload["portfolio_id"],
        )

    def _refresh_portfolio(self, command: ApplicationCommand):
        request = command.payload.get("request")
        if request is None:
            raise InvalidApplicationInput("refresh requires request payload")
        return self._portfolio.refresh_portfolio(command.session_id, request)

    def _generate_recommendation(self, command: ApplicationCommand):
        request = command.payload.get("request")
        if request is None:
            raise InvalidApplicationInput("recommendation requires request payload")
        return self._ai.generate_recommendation(command.session_id, request)
