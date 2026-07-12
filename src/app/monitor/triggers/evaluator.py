"""Trigger evaluation against engine outputs."""

from datetime import datetime, timezone
from decimal import Decimal

from app.monitor.models.alert import AlertRule, AlertTrigger
from app.monitor.models.enums import RuleType, TriggerType
from app.monitor.models.request import MonitorAnalysisRequest
from app.utils.uuid_helper import generate_uuid


class TriggerEvaluator:
    """Evaluate rules and produce triggers (no pricing/greeks calculation)."""

    def evaluate(
        self,
        request: MonitorAnalysisRequest,
        rules: tuple[AlertRule, ...],
    ) -> tuple[AlertTrigger, ...]:
        """Evaluate all rules against request data."""
        triggers: list[AlertTrigger] = []
        for rule in rules:
            trigger = self._evaluate_rule(request, rule)
            if trigger is not None:
                triggers.append(trigger)
        return tuple(triggers)

    def _evaluate_rule(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        handlers = {
            RuleType.MAX_LOSS: self._loss_trigger,
            RuleType.MAX_PROFIT: self._profit_trigger,
            RuleType.MAX_DELTA: self._delta_trigger,
            RuleType.MAX_GAMMA: self._gamma_trigger,
            RuleType.MAX_VEGA: self._vega_trigger,
            RuleType.MAX_THETA: self._theta_trigger,
            RuleType.MAX_MARGIN: self._margin_trigger,
            RuleType.MAX_DRAWDOWN: self._drawdown_trigger,
            RuleType.TIME_TO_EXPIRY: self._expiry_trigger,
            RuleType.IV_SPIKE: self._iv_spike_trigger,
            RuleType.IV_CRUSH: self._iv_crush_trigger,
            RuleType.OI_SHIFT: self._oi_shift_trigger,
            RuleType.PRICE_GAP: self._price_gap_trigger,
        }
        handler = handlers.get(rule.rule_type, self._custom_trigger)
        return handler(request, rule)

    def _loss_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        pnl = request.portfolio_result.unrealized_pnl
        if pnl <= rule.threshold:
            return self._build(rule, TriggerType.LOSS_THRESHOLD, pnl, rule.symbol)
        return None

    def _profit_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        pnl = request.portfolio_result.unrealized_pnl
        if pnl >= rule.threshold:
            return self._build(rule, TriggerType.PROFIT_TARGET, pnl, rule.symbol)
        return None

    def _delta_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        risk = request.risk_result
        if risk is None:
            return None
        value = abs(risk.net_delta)
        if value >= rule.threshold:
            return self._build(rule, TriggerType.DELTA_LIMIT, value, rule.symbol)
        return None

    def _gamma_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        risk = request.risk_result
        if risk is None:
            return None
        value = abs(risk.net_gamma)
        if value >= rule.threshold:
            return self._build(rule, TriggerType.GAMMA_LIMIT, value, rule.symbol)
        return None

    def _vega_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        risk = request.risk_result
        if risk is None:
            return None
        value = abs(risk.net_vega)
        if value >= rule.threshold:
            return self._build(rule, TriggerType.VOLATILITY_SPIKE, value, rule.symbol)
        return None

    def _theta_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        risk = request.risk_result
        if risk is None:
            return None
        value = risk.net_theta
        if value <= rule.threshold:
            return self._build(rule, TriggerType.THETA_DECAY, value, rule.symbol)
        return None

    def _margin_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        margin = request.margin_result
        if margin is None:
            return None
        value = margin.margin_utilization
        if value >= rule.threshold:
            return self._build(rule, TriggerType.MARGIN_LIMIT, value, rule.symbol)
        return None

    def _drawdown_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        risk = request.risk_result
        if risk is None:
            dd = request.portfolio_result.performance_summary.drawdown
        else:
            dd = risk.maximum_drawdown
        if dd >= rule.threshold:
            return self._build(rule, TriggerType.LOSS_THRESHOLD, dd, rule.symbol)
        return None

    def _expiry_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        ctx = self._strategy_context(request)
        if ctx is None:
            return None
        days = Decimal(str(ctx.calculation_context.days_to_expiry))
        if days <= rule.threshold:
            return self._build(rule, TriggerType.EXPIRY_WARNING, days, rule.symbol)
        return None

    def _iv_spike_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        risk = request.risk_result
        if risk is not None and risk.portfolio_volatility >= rule.threshold:
            return self._build(
                rule,
                TriggerType.VOLATILITY_SPIKE,
                risk.portfolio_volatility,
                rule.symbol,
            )
        ctx = self._strategy_context(request)
        if ctx is None:
            return None
        iv = ctx.calculation_context.implied_volatility
        hist = ctx.calculation_context.historical_volatility
        if iv is None or hist is None:
            return None
        change = iv - hist
        if change >= rule.threshold:
            return self._build(rule, TriggerType.VOLATILITY_SPIKE, change, rule.symbol)
        return None

    def _iv_crush_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        ctx = self._strategy_context(request)
        if ctx is None:
            return None
        iv = ctx.calculation_context.implied_volatility
        hist = ctx.calculation_context.historical_volatility
        if iv is None or hist is None:
            return None
        change = iv - hist
        if change <= rule.threshold:
            return self._build(rule, TriggerType.VOLATILITY_SPIKE, change, rule.symbol)
        return None

    def _oi_shift_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        for event in request.market_events:
            if event.event_name == "OptionChainUpdatedEvent":
                return self._build(
                    rule, TriggerType.CUSTOM, rule.threshold, event.symbol
                )
        return None

    def _price_gap_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        for event in request.market_events:
            if event.event_name == "QuoteUpdatedEvent":
                return self._build(
                    rule, TriggerType.CUSTOM, rule.threshold, event.symbol
                )
        return None

    def _custom_trigger(
        self,
        request: MonitorAnalysisRequest,
        rule: AlertRule,
    ) -> AlertTrigger | None:
        if not rule.custom_expression:
            return None
        return self._build(
            rule,
            TriggerType.CUSTOM,
            request.portfolio_result.unrealized_pnl,
            rule.symbol,
        )

    def _strategy_context(self, request: MonitorAnalysisRequest):
        if request.strategy_evaluation is None:
            return None
        return request.strategy_evaluation.analysis.context

    def _build(
        self,
        rule: AlertRule,
        trigger_type: TriggerType,
        observed: Decimal,
        symbol: str,
    ) -> AlertTrigger:
        return AlertTrigger(
            trigger_id=generate_uuid(),
            trigger_type=trigger_type,
            rule_id=rule.rule_id,
            symbol=symbol,
            observed_value=observed,
            threshold=rule.threshold,
            triggered_at=datetime.now(timezone.utc),
        )
