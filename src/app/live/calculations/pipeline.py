"""Orchestrate frozen quantitative engines for live analytics."""

from datetime import datetime, timezone

from app.live.calculations.context_builder import LiveContextBuilder
from app.live.exceptions import LiveCalculationException
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.chain_key import ChainKey
from app.margin.models.request import MarginAnalysisRequest
from app.option_chain.models.request import OptionChainAnalysisRequest
from app.payoff.models.request import PayoffAnalysisRequest
from app.probability.models.request import ProbabilityAnalysisRequest
from app.risk.models.request import RiskAnalysisRequest
from app.strategy.engine.bundle import EngineBundle
from app.volatility.models.request import VolatilityAnalysisRequest


class LiveCalculationPipeline:
    """Run frozen engines in dependency order."""

    def __init__(self, engines: EngineBundle, context_builder: LiveContextBuilder) -> None:
        self._engines = engines
        self._context_builder = context_builder

    def run(self, key: ChainKey) -> LiveAnalyticsSnapshot:
        try:
            return self._execute(key)
        except Exception as error:
            raise LiveCalculationException(str(error)) from error

    def _execute(self, key: ChainKey) -> LiveAnalyticsSnapshot:
        ctx = self._context_builder.build_context(key)
        contract = self._context_builder.build_contract(key, ctx)
        option_chain = self._context_builder.build_option_chain(key, ctx)
        market_snapshot = self._context_builder.build_market_snapshot(key, ctx)
        chain_market = self._context_builder.build_chain_market_snapshot(key, ctx)
        vol_market = self._context_builder.build_volatility_snapshot(key, ctx)
        historical = self._context_builder.build_historical_snapshot(key)
        portfolio = self._context_builder.build_portfolio(ctx)
        resolved_legs = portfolio.legs

        pricing = self._engines.pricing.price(ctx, contract)
        greeks = self._engines.greeks.calculate_greeks(ctx, contract, pricing)
        volatility = self._engines.volatility.calculate(
            VolatilityAnalysisRequest(
                context=ctx,
                pricing_result=pricing,
                greeks_result=greeks,
                market_snapshot=vol_market,
                historical_data=historical,
                option_chain=option_chain,
            )
        )
        chain_analysis = self._engines.option_chain.analyze(
            OptionChainAnalysisRequest(
                context=ctx,
                option_chain=option_chain,
                greeks_result=greeks,
                volatility_result=volatility,
                market_snapshot=chain_market,
            )
        )
        probability = self._engines.probability.calculate(
            ProbabilityAnalysisRequest(
                context=ctx,
                pricing_result=pricing,
                greeks_result=greeks,
                volatility_result=volatility,
                chain_analysis=chain_analysis,
            )
        )
        payoff = risk = margin = None
        if resolved_legs:
            payoff = self._engines.payoff.calculate(
                PayoffAnalysisRequest(
                    context=ctx,
                    pricing_result=pricing,
                    greeks_result=greeks,
                    volatility_result=volatility,
                    probability_result=probability,
                    legs=resolved_legs,
                    portfolio=portfolio,
                )
            )
            risk = self._engines.risk.calculate(
                RiskAnalysisRequest(
                    context=ctx,
                    pricing_result=pricing,
                    greeks_result=greeks,
                    volatility_result=volatility,
                    probability_result=probability,
                    payoff_result=payoff,
                    legs=resolved_legs,
                    market_snapshot=market_snapshot,
                    portfolio=portfolio,
                )
            )
            margin = self._engines.margin.calculate(
                MarginAnalysisRequest(
                    context=ctx,
                    legs=resolved_legs,
                    risk_result=risk,
                    payoff_result=payoff,
                    market_snapshot=market_snapshot,
                    portfolio=portfolio,
                )
            )
        return LiveAnalyticsSnapshot(
            underlying=key.underlying,
            exchange=key.exchange,
            expiry_date=key.expiry_date,
            spot_price=ctx.spot_price,
            pricing=pricing,
            greeks=greeks,
            volatility=volatility,
            chain_analysis=chain_analysis,
            probability=probability,
            payoff=payoff,
            risk=risk,
            margin=margin,
            portfolio_greeks=self._extract_greeks(greeks),
            position_greeks=self._extract_greeks(greeks),
            calculation_timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _extract_greeks(greeks) -> dict[str, object]:
        return {
            "delta": getattr(greeks, "delta", None),
            "gamma": getattr(greeks, "gamma", None),
            "theta": getattr(greeks, "theta", None),
            "vega": getattr(greeks, "vega", None),
        }
