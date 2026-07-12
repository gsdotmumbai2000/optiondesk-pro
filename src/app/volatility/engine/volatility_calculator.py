"""Volatility calculator."""

from datetime import datetime, timezone
from decimal import Decimal

from app.volatility.analytics.expected_move import expected_move as calc_expected_move
from app.volatility.analytics.implied_vol import resolve_implied_volatility
from app.volatility.analytics.iv_percentile import iv_percentile as calc_iv_percentile
from app.volatility.analytics.realized_vol import (
    historical_volatility,
    realized_volatility,
)
from app.volatility.models.enums import VolatilityModelVersion
from app.volatility.models.request import VolatilityAnalysisRequest
from app.volatility.models.volatility_result import ExpectedMove, VolatilityResult


class VolatilityCalculator:
    """Calculate full volatility analytics from request bundle."""

    def calculate(self, request: VolatilityAnalysisRequest) -> VolatilityResult:
        """Compute VolatilityResult from request."""
        ctx = request.context
        implied = resolve_implied_volatility(ctx, request.option_chain)
        realized = realized_volatility(request.historical_data, ctx)
        hist = historical_volatility(realized, ctx)
        to_expiry, one_day = calc_expected_move(ctx.spot_price, implied, ctx)
        percentile = calc_iv_percentile(implied, hist)
        annualized = implied * Decimal("15.8745") if implied > 0 else Decimal("0")

        return VolatilityResult(
            implied_volatility=implied,
            annualized_volatility=annualized,
            realized_volatility=realized,
            historical_volatility=hist,
            expected_move=ExpectedMove(to_expiry=to_expiry, one_day=one_day),
            iv_percentile=percentile,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=VolatilityModelVersion.V1,
        )
