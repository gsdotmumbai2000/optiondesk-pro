"""Risk report data models."""

from dataclasses import dataclass
from decimal import Decimal

from app.risk.models.exposure import PortfolioExposure
from app.risk.models.limits import RiskLimitWarning
from app.risk.models.stress import StressTestResult
from app.risk.models.var import CVaRResult, VaRResult


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """High-level risk summary report."""

    risk_score: Decimal
    capital_at_risk: Decimal
    value_at_risk: Decimal
    expected_shortfall: Decimal
    net_delta: Decimal
    net_gamma: Decimal
    net_vega: Decimal


@dataclass(frozen=True, slots=True)
class ExposureSummary:
    """Portfolio exposure summary report."""

    exposure: PortfolioExposure
    concentration: Decimal


@dataclass(frozen=True, slots=True)
class VaRReport:
    """VaR report across methods and confidence levels."""

    results: tuple[VaRResult, ...]
    cvar_results: tuple[CVaRResult, ...]


@dataclass(frozen=True, slots=True)
class StressReport:
    """Stress test report."""

    results: tuple[StressTestResult, ...]
    worst_stress_loss: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioReport:
    """Full portfolio risk report."""

    summary: RiskSummary
    exposure_summary: ExposureSummary
    var_report: VaRReport
    stress_report: StressReport
    limit_warnings: tuple[RiskLimitWarning, ...]
