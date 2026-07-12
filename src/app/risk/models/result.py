"""Risk analysis result."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.risk.models.enums import RiskModelVersion
from app.risk.models.exposure import PortfolioExposure
from app.risk.models.limits import RiskLimitWarning
from app.risk.models.stress import StressTestResult
from app.risk.models.var import CVaRResult, VaRResult


@dataclass(frozen=True, slots=True)
class RiskResult:
    """Immutable risk analytics output."""

    net_delta: Decimal
    net_gamma: Decimal
    net_theta: Decimal
    net_vega: Decimal
    net_rho: Decimal
    net_vanna: Decimal
    net_charm: Decimal
    net_vomma: Decimal
    portfolio_beta: Decimal
    portfolio_volatility: Decimal
    maximum_drawdown: Decimal
    value_at_risk: Decimal
    expected_shortfall: Decimal
    stress_loss: Decimal
    scenario_loss: Decimal
    risk_score: Decimal
    capital_at_risk: Decimal
    risk_reward_ratio: Decimal | None
    margin_utilization_estimate: Decimal
    portfolio_concentration: Decimal
    portfolio_exposure: PortfolioExposure
    var_results: tuple[VaRResult, ...]
    cvar_results: tuple[CVaRResult, ...]
    stress_results: tuple[StressTestResult, ...]
    limit_warnings: tuple[RiskLimitWarning, ...]
    calculation_timestamp: datetime
    model_version: RiskModelVersion = RiskModelVersion.V1
