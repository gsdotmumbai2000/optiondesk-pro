"""Portfolio risk calculator."""

from datetime import datetime, timezone
from decimal import Decimal

from app.risk.analytics.capital_at_risk import capital_at_risk as calc_capital_at_risk
from app.risk.analytics.concentration import portfolio_concentration
from app.risk.analytics.drawdown import maximum_drawdown
from app.risk.analytics.expected_shortfall import expected_shortfall
from app.risk.analytics.greeks_aggregation import aggregate_greeks
from app.risk.analytics.margin_estimate import margin_utilization_estimate
from app.risk.analytics.portfolio_beta import portfolio_beta
from app.risk.analytics.portfolio_volatility import portfolio_volatility
from app.risk.analytics.risk_score import risk_score
from app.risk.analytics.var_historical import historical_var
from app.risk.analytics.var_parametric import parametric_var
from app.risk.analytics.var_variance_covariance import variance_covariance_var
from app.risk.limits.limit_checker import check_limits
from app.risk.models.enums import ConfidenceLevel, RiskModelVersion
from app.risk.models.limits import RiskLimitConfig
from app.risk.models.request import RiskAnalysisRequest
from app.risk.models.result import RiskResult
from app.risk.portfolio.exposure_calculator import calculate_exposure
from app.risk.stress.stress_runner import run_all_stress_tests
from app.risk.stress.stress_scenarios import all_stress_scenarios


class PortfolioRiskCalculator:
    """Calculate full portfolio risk metrics."""

    def calculate(
        self,
        request: RiskAnalysisRequest,
        limits: RiskLimitConfig | None = None,
    ) -> RiskResult:
        """Compute RiskResult from request bundle."""
        legs = request.resolved_legs
        ctx = request.context
        greeks = request.greeks_result
        vol = request.volatility_result
        payoff = request.payoff_result

        agg = aggregate_greeks(legs, ctx, greeks)
        port_vol = portfolio_volatility(vol, agg["delta"])
        port_beta = portfolio_beta(ctx, greeks, agg["delta"])
        exposure = calculate_exposure(legs)
        concentration = portfolio_concentration(legs)
        port_value = exposure.total_notional or ctx.spot_price

        var_results = self._compute_var(port_value, port_vol, ctx, vol)
        primary_var = var_results[0].value_at_risk
        cvar_results = tuple(
            expected_shortfall(v.value_at_risk, port_vol, v.confidence)
            for v in var_results
        )
        primary_cvar = cvar_results[0].expected_shortfall

        base_pnl = payoff.current_pnl
        stress_results = run_all_stress_tests(
            all_stress_scenarios(), legs, ctx, vol, base_pnl
        )
        worst_stress = max((s.stress_loss for s in stress_results), default=Decimal("0"))

        car = calc_capital_at_risk(payoff, primary_var)
        margin_est = margin_utilization_estimate(legs, ctx, car)
        mdd = maximum_drawdown(payoff)
        score = risk_score(primary_var, primary_cvar, port_vol, concentration)
        position_size = sum(abs(leg.quantity) for leg in legs)

        limit_warnings = ()
        if limits is not None:
            limit_warnings = check_limits(
                limits,
                net_delta=agg["delta"],
                net_gamma=agg["gamma"],
                net_vega=agg["vega"],
                current_pnl=payoff.current_pnl,
                margin_utilization=margin_est,
                position_size=position_size,
                capital_exposure=car,
            )

        return RiskResult(
            net_delta=agg["delta"],
            net_gamma=agg["gamma"],
            net_theta=agg["theta"],
            net_vega=agg["vega"],
            net_rho=agg["rho"],
            net_vanna=agg["vanna"],
            net_charm=agg["charm"],
            net_vomma=agg["vomma"],
            portfolio_beta=port_beta,
            portfolio_volatility=port_vol,
            maximum_drawdown=mdd,
            value_at_risk=primary_var,
            expected_shortfall=primary_cvar,
            stress_loss=worst_stress,
            scenario_loss=worst_stress,
            risk_score=score,
            capital_at_risk=car,
            risk_reward_ratio=payoff.risk_reward_ratio,
            margin_utilization_estimate=margin_est,
            portfolio_concentration=concentration,
            portfolio_exposure=exposure,
            var_results=var_results,
            cvar_results=cvar_results,
            stress_results=stress_results,
            limit_warnings=limit_warnings,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=RiskModelVersion.V1,
        )

    def _compute_var(self, port_value, port_vol, ctx, vol):
        levels = (ConfidenceLevel.P95, ConfidenceLevel.P99)
        results = []
        for level in levels:
            results.append(parametric_var(port_value, port_vol, level))
            results.append(historical_var(port_value, ctx, vol, level))
            results.append(variance_covariance_var(port_value, port_vol, level))
        return tuple(results)
