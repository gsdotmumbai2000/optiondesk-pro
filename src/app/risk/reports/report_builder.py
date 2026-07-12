"""Risk report builder."""

from decimal import Decimal

from app.risk.models.exposure import PortfolioExposure
from app.risk.models.limits import RiskLimitWarning
from app.risk.models.reports import (
    ExposureSummary,
    PortfolioReport,
    RiskSummary,
    StressReport,
    VaRReport,
)
from app.risk.models.result import RiskResult
from app.risk.models.stress import StressTestResult
from app.risk.models.var import CVaRResult, VaRResult


class ReportBuilder:
    """Build risk report data models from RiskResult."""

    def build_summary(self, result: RiskResult) -> RiskSummary:
        """Build risk summary report."""
        return RiskSummary(
            risk_score=result.risk_score,
            capital_at_risk=result.capital_at_risk,
            value_at_risk=result.value_at_risk,
            expected_shortfall=result.expected_shortfall,
            net_delta=result.net_delta,
            net_gamma=result.net_gamma,
            net_vega=result.net_vega,
        )

    def build_exposure_summary(
        self,
        exposure: PortfolioExposure,
        concentration: Decimal,
    ) -> ExposureSummary:
        """Build exposure summary report."""
        return ExposureSummary(exposure=exposure, concentration=concentration)

    def build_var_report(
        self,
        var_results: tuple[VaRResult, ...],
        cvar_results: tuple[CVaRResult, ...],
    ) -> VaRReport:
        """Build VaR report."""
        return VaRReport(results=var_results, cvar_results=cvar_results)

    def build_stress_report(
        self,
        stress_results: tuple[StressTestResult, ...],
    ) -> StressReport:
        """Build stress test report."""
        worst = max((r.stress_loss for r in stress_results), default=Decimal("0"))
        return StressReport(results=stress_results, worst_stress_loss=worst)

    def build_portfolio_report(self, result: RiskResult) -> PortfolioReport:
        """Build full portfolio risk report."""
        return PortfolioReport(
            summary=self.build_summary(result),
            exposure_summary=self.build_exposure_summary(
                result.portfolio_exposure,
                result.portfolio_concentration,
            ),
            var_report=self.build_var_report(result.var_results, result.cvar_results),
            stress_report=self.build_stress_report(result.stress_results),
            limit_warnings=result.limit_warnings,
        )
