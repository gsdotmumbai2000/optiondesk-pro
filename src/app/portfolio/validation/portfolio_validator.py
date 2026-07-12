"""Portfolio input validation."""

from app.portfolio.exceptions import InvalidPortfolioInput
from app.portfolio.models.portfolio import Portfolio
from app.portfolio.models.request import PortfolioAnalysisRequest
from app.portfolio.models.transactions import Trade


class PortfolioValidator:
    """Validate portfolio inputs and integrity."""

    def validate_request(self, request: PortfolioAnalysisRequest) -> None:
        """Validate analysis request."""
        if not request.portfolio_id:
            raise InvalidPortfolioInput("portfolio_id is required")
        for trade in request.trade_executions:
            self._validate_trade(trade)

    def validate_portfolio(self, portfolio: Portfolio) -> None:
        """Validate portfolio integrity."""
        if not portfolio.portfolio_id:
            raise InvalidPortfolioInput("portfolio must have portfolio_id")
        if portfolio.cash_account.balance < 0:
            raise InvalidPortfolioInput("cash balance cannot be negative")
        self._validate_cash_integrity(portfolio)

    def _validate_trade(self, trade: Trade) -> None:
        if not trade.symbol:
            raise InvalidPortfolioInput("trade symbol is required")
        if trade.quantity == 0:
            raise InvalidPortfolioInput("trade quantity cannot be zero")
        if trade.price <= 0:
            raise InvalidPortfolioInput("trade price must be positive")

    def _validate_cash_integrity(self, portfolio: Portfolio) -> None:
        cash = portfolio.cash_account
        if cash.available > cash.balance:
            raise InvalidPortfolioInput("available cash exceeds balance")
        if cash.reserved < 0:
            raise InvalidPortfolioInput("reserved cash cannot be negative")
