"""Risk engine entry point."""

from app.risk.engine.portfolio_risk_calculator import PortfolioRiskCalculator
from app.risk.engine.stress_calculator import StressCalculator
from app.risk.engine.var_calculator import VaRCalculator
from app.risk.models.limits import RiskLimitConfig
from app.risk.models.request import RiskAnalysisRequest
from app.risk.models.result import RiskResult


class RiskEngine:
    """Enterprise risk engine."""

    def __init__(
        self,
        portfolio_calculator: PortfolioRiskCalculator | None = None,
        var_calculator: VaRCalculator | None = None,
        stress_calculator: StressCalculator | None = None,
    ) -> None:
        """Initialize engine."""
        self._portfolio = portfolio_calculator or PortfolioRiskCalculator()
        self._var = var_calculator or VaRCalculator()
        self._stress = stress_calculator or StressCalculator()

    @property
    def portfolio_calculator(self) -> PortfolioRiskCalculator:
        """Return portfolio risk calculator."""
        return self._portfolio

    @property
    def var_calculator(self) -> VaRCalculator:
        """Return VaR calculator."""
        return self._var

    @property
    def stress_calculator(self) -> StressCalculator:
        """Return stress calculator."""
        return self._stress

    def calculate(
        self,
        request: RiskAnalysisRequest,
        limits: RiskLimitConfig | None = None,
    ) -> RiskResult:
        """Calculate portfolio risk analytics."""
        return self._portfolio.calculate(request, limits)
