"""Option chain analyzer."""

from datetime import datetime, timezone

from app.option_chain.analytics.liquidity import liquidity_score
from app.option_chain.analytics.put_call_ratio import put_call_ratio
from app.option_chain.analytics.skew import atm_iv, skew
from app.option_chain.models.analysis import OptionChainAnalysis
from app.option_chain.models.enums import OptionChainModelVersion
from app.option_chain.models.request import OptionChainAnalysisRequest


class OptionChainAnalyzer:
    """Calculate option chain analytics from request bundle."""

    def analyze(self, request: OptionChainAnalysisRequest) -> OptionChainAnalysis:
        """Compute OptionChainAnalysis from request."""
        chain = request.option_chain
        liquidity = liquidity_score(chain)
        ratio, call_oi, put_oi = put_call_ratio(chain)
        atm = atm_iv(chain, request.volatility_result)
        chain_skew = skew(chain, atm)
        return OptionChainAnalysis(
            liquidity_score=liquidity,
            put_call_ratio=ratio,
            atm_iv=atm,
            total_call_oi=call_oi,
            total_put_oi=put_oi,
            skew=chain_skew,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=OptionChainModelVersion.V1,
        )
