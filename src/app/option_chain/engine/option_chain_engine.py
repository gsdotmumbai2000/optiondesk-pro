"""Option chain engine entry point."""

from app.option_chain.engine.chain_analyzer import OptionChainAnalyzer
from app.option_chain.models.analysis import OptionChainAnalysis
from app.option_chain.models.request import OptionChainAnalysisRequest


class OptionChainEngine:
    """Enterprise option chain analytics engine."""

    def __init__(self, analyzer: OptionChainAnalyzer | None = None) -> None:
        """Initialize engine."""
        self._analyzer = analyzer or OptionChainAnalyzer()

    @property
    def analyzer(self) -> OptionChainAnalyzer:
        """Return option chain analyzer."""
        return self._analyzer

    def analyze(self, request: OptionChainAnalysisRequest) -> OptionChainAnalysis:
        """Analyze option chain."""
        return self._analyzer.analyze(request)
