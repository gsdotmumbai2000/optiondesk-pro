"""Report builder."""

from app.portfolio.models.reports import (
    AllocationReport,
    PerformanceReport,
    PnLReport,
    PortfolioReport,
    TransactionReport,
)
from app.portfolio.models.result import PortfolioResult


class ReportBuilder:
    """Build portfolio report data models."""

    def build_portfolio_report(self, result: PortfolioResult) -> PortfolioReport:
        """Build portfolio summary report."""
        return PortfolioReport(
            portfolio_id="",
            portfolio_value=str(result.portfolio_value),
            cash_balance=str(result.cash_balance),
        )

    def build_transaction_report(
        self,
        result: PortfolioResult,
    ) -> TransactionReport:
        """Build transaction report."""
        txs = result.transaction_history
        return TransactionReport(transactions=txs, total_count=len(txs))

    def build_pnl_report(self, result: PortfolioResult) -> PnLReport:
        """Build PnL report."""
        return PnLReport(
            realized_pnl=str(result.realized_pnl),
            unrealized_pnl=str(result.unrealized_pnl),
            todays_pnl=str(result.todays_pnl),
        )

    def build_allocation_report(
        self,
        result: PortfolioResult,
    ) -> AllocationReport:
        """Build allocation report."""
        return AllocationReport(allocation=result.allocation)

    def build_performance_report(
        self,
        result: PortfolioResult,
    ) -> PerformanceReport:
        """Build performance report."""
        return PerformanceReport(performance=result.performance_summary)
