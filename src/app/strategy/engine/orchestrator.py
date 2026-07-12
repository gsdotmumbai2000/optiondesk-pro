"""Engine orchestrator — delegates to frozen engines only."""

from app.margin.models.request import MarginAnalysisRequest
from app.option_chain.models.request import OptionChainAnalysisRequest
from app.payoff.models.legs import PortfolioPosition
from app.payoff.models.request import PayoffAnalysisRequest
from app.probability.models.request import ProbabilityAnalysisRequest
from app.risk.models.request import RiskAnalysisRequest
from app.strategy.builders.leg_converter import to_payoff_legs
from app.strategy.engine.bundle import EngineBundle
from app.strategy.models.context import StrategyContext
from app.strategy.models.request import StrategyEvaluationRequest
from app.volatility.models.request import VolatilityAnalysisRequest


class EngineOrchestrator:
    """Orchestrate calls to quantitative engines in dependency order."""

    def __init__(self, engines: EngineBundle) -> None:
        """Initialize with injected engine bundle."""
        self._engines = engines

    def orchestrate(self, request: StrategyEvaluationRequest) -> StrategyContext:
        """Run all engines and return strategy context."""
        ctx = request.calculation_context
        contract = request.option_contract

        pricing = self._engines.pricing.price(ctx, contract)
        greeks = self._engines.greeks.calculate_greeks(ctx, contract, pricing)

        vol_request = VolatilityAnalysisRequest(
            context=ctx,
            pricing_result=pricing,
            greeks_result=greeks,
            market_snapshot=request.volatility_market_snapshot,
            historical_data=request.historical_data,
            option_chain=request.option_chain,
        )
        volatility = self._engines.volatility.calculate(vol_request)

        chain_request = OptionChainAnalysisRequest(
            context=ctx,
            option_chain=request.option_chain,
            greeks_result=greeks,
            volatility_result=volatility,
            market_snapshot=request.chain_market_snapshot,
        )
        chain_analysis = self._engines.option_chain.analyze(chain_request)

        prob_request = ProbabilityAnalysisRequest(
            context=ctx,
            pricing_result=pricing,
            greeks_result=greeks,
            volatility_result=volatility,
            chain_analysis=chain_analysis,
        )
        probability = self._engines.probability.calculate(prob_request)

        payoff_legs = to_payoff_legs(request.legs, ctx)
        portfolio = request.portfolio or PortfolioPosition(legs=payoff_legs)
        payoff_request = PayoffAnalysisRequest(
            context=ctx,
            pricing_result=pricing,
            greeks_result=greeks,
            volatility_result=volatility,
            probability_result=probability,
            legs=payoff_legs,
            portfolio=portfolio,
        )
        payoff = self._engines.payoff.calculate(payoff_request)

        risk_request = RiskAnalysisRequest(
            context=ctx,
            pricing_result=pricing,
            greeks_result=greeks,
            volatility_result=volatility,
            probability_result=probability,
            payoff_result=payoff,
            legs=payoff_legs,
            market_snapshot=request.market_snapshot,
            portfolio=portfolio,
        )
        risk = self._engines.risk.calculate(risk_request)

        margin_request = MarginAnalysisRequest(
            context=ctx,
            legs=payoff_legs,
            risk_result=risk,
            payoff_result=payoff,
            market_snapshot=request.market_snapshot,
            broker_response=request.broker_response,
            portfolio=portfolio,
        )
        margin = self._engines.margin.calculate(margin_request)

        return StrategyContext(
            calculation_context=ctx,
            pricing_result=pricing,
            greeks_result=greeks,
            volatility_result=volatility,
            probability_result=probability,
            payoff_result=payoff,
            risk_result=risk,
            margin_result=margin,
            legs=request.legs,
            market_snapshot=request.market_snapshot,
            portfolio=portfolio,
        )
