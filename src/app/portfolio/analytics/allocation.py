"""Portfolio allocation calculator."""

from decimal import Decimal

from app.portfolio.models.enums import AssetClass
from app.portfolio.models.performance import AllocationSlice, PortfolioAllocation
from app.portfolio.models.positions import Holding


class AllocationCalculator:
    """Compute allocation breakdowns from holdings."""

    def calculate(self, holdings: tuple[Holding, ...]) -> PortfolioAllocation:
        """Build allocation slices from holdings."""
        total = sum(h.market_value for h in holdings) or Decimal("1")
        asset = self._by_asset(holdings, total)
        underlying = self._by_underlying(holdings, total)
        capital = self._by_capital(holdings, total)
        return PortfolioAllocation(
            asset=asset,
            underlying=underlying,
            sector=(),
            expiry=(),
            capital=capital,
        )

    def _by_asset(
        self,
        holdings: tuple[Holding, ...],
        total: Decimal,
    ) -> tuple[AllocationSlice, ...]:
        buckets: dict[str, Decimal] = {}
        for h in holdings:
            label = h.asset_class.value
            buckets[label] = buckets.get(label, Decimal("0")) + h.market_value
        return self._slices(buckets, total)

    def _by_underlying(
        self,
        holdings: tuple[Holding, ...],
        total: Decimal,
    ) -> tuple[AllocationSlice, ...]:
        buckets: dict[str, Decimal] = {}
        for h in holdings:
            label = h.underlying or h.symbol
            buckets[label] = buckets.get(label, Decimal("0")) + h.market_value
        return self._slices(buckets, total)

    def _by_capital(
        self,
        holdings: tuple[Holding, ...],
        total: Decimal,
    ) -> tuple[AllocationSlice, ...]:
        cash = sum(
            h.market_value for h in holdings if h.asset_class == AssetClass.CASH
        )
        invested = total - cash
        return (
            AllocationSlice(
                label="cash",
                weight=cash / total,
                notional=cash,
            ),
            AllocationSlice(
                label="invested",
                weight=invested / total,
                notional=invested,
            ),
        )

    def _slices(
        self,
        buckets: dict[str, Decimal],
        total: Decimal,
    ) -> tuple[AllocationSlice, ...]:
        return tuple(
            AllocationSlice(
                label=label,
                weight=notional / total,
                notional=notional,
            )
            for label, notional in sorted(buckets.items())
        )
