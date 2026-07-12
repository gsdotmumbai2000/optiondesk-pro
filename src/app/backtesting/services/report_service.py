"""Report service."""

from app.backtesting.models.reports import BacktestReport
from app.backtesting.models.result import BacktestResult
from app.backtesting.reports.report_builder import ReportBuilder


class ReportService:
    """Generate backtest reports."""

    def __init__(self, builder: ReportBuilder | None = None) -> None:
        """Initialize report service."""
        self._builder = builder or ReportBuilder()

    def build(self, result: BacktestResult) -> BacktestReport:
        """Build backtest report."""
        return self._builder.build(result)
