"""Risk application service."""

from app.events.event_bus import EventBus
from app.risk.cache.risk_cache import RiskCache
from app.risk.engine.portfolio_risk_calculator import PortfolioRiskCalculator
from app.risk.engine.risk_engine import RiskEngine
from app.risk.events import (
    PortfolioUpdatedEvent,
    RiskCalculatedEvent,
    RiskLimitExceededEvent,
    StressCompletedEvent,
    VaRUpdatedEvent,
)
from app.risk.exceptions import RiskException
from app.risk.models.limits import RiskLimitConfig
from app.risk.models.request import RiskAnalysisRequest
from app.risk.models.result import RiskResult
from app.risk.models.scenario import RiskScenario
from app.risk.providers.cache_keys import build_cache_key
from app.risk.reports.report_builder import ReportBuilder
from app.risk.services.scenario_service import ScenarioService
from app.risk.validation.risk_validator import RiskValidator


class RiskService:
    """Orchestrate risk analytics, caching, and events."""

    def __init__(
        self,
        engine: RiskEngine,
        validator: RiskValidator | None = None,
        cache: RiskCache | None = None,
        event_bus: EventBus | None = None,
        scenario_service: ScenarioService | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or RiskValidator()
        self._cache = cache or RiskCache()
        self._event_bus = event_bus
        self._scenario_service = scenario_service or ScenarioService()
        self._report_builder = ReportBuilder()

    @property
    def cache(self) -> RiskCache:
        """Return risk cache."""
        return self._cache

    @property
    def portfolio_calculator(self) -> PortfolioRiskCalculator:
        """Return portfolio risk calculator."""
        return self._engine.portfolio_calculator

    def calculate(
        self,
        request: RiskAnalysisRequest,
        limits: RiskLimitConfig | None = None,
    ) -> RiskResult:
        """Calculate and cache risk analytics."""
        try:
            self._validator.validate(request)
            result = self._engine.calculate(request, limits)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_events(key, result)
            return result
        except RiskException:
            raise

    def get_latest(self, request: RiskAnalysisRequest) -> RiskResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(
        self,
        request: RiskAnalysisRequest,
        limits: RiskLimitConfig | None = None,
    ) -> RiskResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.calculate(request, limits)

    def build_report(self, result: RiskResult):
        """Build full portfolio risk report."""
        return self._report_builder.build_portfolio_report(result)

    def run_scenarios(
        self,
        request: RiskAnalysisRequest,
        scenarios: tuple[RiskScenario, ...],
    ):
        """Run risk scenarios and return ranked results."""
        self._validator.validate(request)
        results = self._scenario_service.run(
            scenarios,
            request.resolved_legs,
            request.context,
            request.payoff_result.current_pnl,
        )
        return self._scenario_service.rank(results)

    def _publish_events(self, key: str, result: RiskResult) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(RiskCalculatedEvent(payload=payload))
        self._event_bus.publish(
            VaRUpdatedEvent(payload={"var": str(result.value_at_risk)})
        )
        self._event_bus.publish(
            StressCompletedEvent(
                payload={"stress_loss": str(result.stress_loss)}
            )
        )
        self._event_bus.publish(PortfolioUpdatedEvent(payload=payload))
        if result.limit_warnings:
            self._event_bus.publish(
                RiskLimitExceededEvent(
                    payload={
                        "warnings": [w.limit_name for w in result.limit_warnings]
                    }
                )
            )
