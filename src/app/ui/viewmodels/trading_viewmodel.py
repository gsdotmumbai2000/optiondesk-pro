"""Trading workspace ViewModel."""

from dataclasses import replace
from datetime import date

from PySide6.QtCore import Property, Signal

from app.application.models.enums import WorkspaceType
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.leg import StrategyLeg
from app.strategy.recognition.recognizer import recognize_strategy
from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class TradingViewModel(BaseViewModel):
    """ViewModel for trading workspace — Application Services only."""

    strategy_name_changed = Signal(str)
    summary_changed = Signal(str)
    margin_summary_changed = Signal(str)
    evaluation_changed = Signal(object)
    optimization_changed = Signal(object)
    paper_trade_changed = Signal(object)
    pending_legs_changed = Signal(list)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        """Initialize trading view model."""
        super().__init__(parent)
        self._ctx = ctx
        self._strategy_name = ""
        self._summary = "No strategy loaded"
        self._margin_summary = "Margin: —"
        self._leg_builder = StrategyBuilder()
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self.evaluate_command = RelayCommand(self.evaluate, parent=self)
        self.optimize_command = RelayCommand(self.optimize, parent=self)
        self.recommend_command = RelayCommand(self.generate_recommendation, parent=self)
        self.refresh_margin_command = RelayCommand(self.refresh_margin, parent=self)
        self.paper_trade_command = RelayCommand(self.paper_trade, parent=self)

    @Property(str, notify=strategy_name_changed)
    def strategy_name(self) -> str:
        return self._strategy_name

    @Property(str, notify=summary_changed)
    def summary(self) -> str:
        return self._summary

    @Property(str, notify=margin_summary_changed)
    def margin_summary(self) -> str:
        return self._margin_summary

    def refresh(self) -> None:
        """Refresh trading workspace view."""
        view = self._ctx.provider.trading.view(self._ctx.session_id)
        self._summary = view.summary
        self.summary_changed.emit(self._summary)
        self.status_message = "Trading workspace refreshed"

    def evaluate(self) -> None:
        """Recompute and publish payoff/Greeks for the strategy currently
        in the builder, by synchronously refreshing live analytics for its
        chain, in the background (the same live engines the tick pipeline
        uses, just run on demand rather than racing it).

        Registers the builder's current legs as this session's active
        strategy first (cache-only, not persisted -- see
        set_active_draft_strategy) so Evaluate works on whatever's in the
        leg table right now, whether loaded from a saved strategy or still
        unsaved -- it shouldn't require clicking Save first just to
        preview one."""
        if not self._register_builder_as_active_strategy():
            return
        self.busy = True

        def work():
            return self._ctx.provider.trading.evaluate_active_strategy(self._ctx.session_id)

        def done(result):
            self.busy = False
            if result is None:
                return
            if not result.success:
                self.status_message = result.message
                return
            self.evaluation_changed.emit(result.data)
            self.status_message = result.message

        def err(msg: str) -> None:
            self.busy = False
            self.set_error(msg)

        self._ctx.worker.run(work, done, err)

    def _register_builder_as_active_strategy(self) -> bool:
        """Make the builder's current legs this session's active Trading
        strategy (see TradingWorkspaceService.set_active_draft_strategy)
        so Evaluate/Optimize/Refresh Margin/Paper Trade can find them.
        Returns False (with a status message) when there are no legs to
        register -- callers should not proceed to their own action."""
        legs = self._leg_builder.legs
        if not legs:
            self.status_message = "Add at least one leg before evaluating"
            return False
        strategy = self._leg_builder.build()
        strategy = replace(
            strategy,
            metadata=replace(strategy.metadata, recognized_type=recognize_strategy(legs)),
        )
        self._ctx.provider.trading.set_active_draft_strategy(self._ctx.session_id, strategy)
        return True

    def refresh_margin(self) -> None:
        """Fetch real broker margin for the active strategy in the
        background (margin_calculator is a REST call, never run on the UI
        thread), falling back to a status message when a broker isn't
        connected or the active strategy has no real margin available."""
        self.busy = True

        def work():
            return self._ctx.provider.trading.refresh_margin(self._ctx.session_id)

        def done(result):
            self.busy = False
            if result is None:
                return
            if not result.success:
                self.status_message = result.message
                return
            response = result.data
            self._margin_summary = (
                f"Margin ({response.broker_id}): "
                f"Span {response.span_margin} | "
                f"Exposure {response.exposure_margin} | "
                f"Total {response.total_margin}"
            )
            self.margin_summary_changed.emit(self._margin_summary)
            self.status_message = result.message

        def err(msg: str) -> None:
            self.busy = False
            self.set_error(msg)

        self._ctx.worker.run(work, done, err)

    def optimize(self) -> None:
        """Search for better variants of the active strategy over its live
        chain, in the background (evaluates many candidates, so it's not
        instant)."""
        self.busy = True

        def work():
            return self._ctx.provider.trading.optimize_active_strategy(self._ctx.session_id)

        def done(result):
            self.busy = False
            if result is None:
                return
            if not result.success:
                self.status_message = result.message
                return
            self.optimization_changed.emit(result.data)
            self.status_message = result.message

        def err(msg: str) -> None:
            self.busy = False
            self.set_error(msg)

        self._ctx.worker.run(work, done, err)

    def paper_trade(self) -> None:
        """Submit the active strategy's legs as paper orders against this
        session's virtual paper account (no broker routing, no capital at
        risk), in the background. Needs no live chain subscription -- each
        leg's own recorded premium is the reference price."""
        self.busy = True

        def work():
            return self._ctx.provider.trading.paper_trade_active_strategy(self._ctx.session_id)

        def done(result):
            self.busy = False
            if result is None:
                return
            if not result.success:
                self.status_message = result.message
                return
            self.paper_trade_changed.emit(result.data)
            self.status_message = result.message

        def err(msg: str) -> None:
            self.busy = False
            self.set_error(msg)

        self._ctx.worker.run(work, done, err)

    def add_leg(self, leg: StrategyLeg) -> None:
        """Add a leg to the strategy currently being built."""
        self._leg_builder.add_leg(leg)
        self.pending_legs_changed.emit(list(self._leg_builder.legs))

    def remove_leg(self, leg_id: str) -> None:
        """Remove a leg from the strategy currently being built."""
        self._leg_builder.remove_leg(leg_id)
        self.pending_legs_changed.emit(list(self._leg_builder.legs))

    def new_strategy(self) -> None:
        """Discard any in-progress legs and start building a fresh strategy."""
        self._leg_builder = StrategyBuilder()
        self.pending_legs_changed.emit([])

    def list_underlyings(self) -> list[str]:
        """Return known underlyings for the Add Leg dialog (pure Instrument
        Master lookup, no broker call -- safe to call directly, no worker)."""
        result = self._ctx.provider.trading.list_underlyings()
        return list(result.data or []) if result.success else []

    def leg_builder_context(self, underlying: str) -> dict:
        """Return {"expiries": [...], "lot_size": int} for the Add Leg
        dialog's expiry dropdown (pure Instrument/Expiry Master lookup, no
        broker call -- safe to call directly, no worker)."""
        result = self._ctx.provider.trading.leg_builder_context(underlying)
        return result.data or {} if result.success else {}

    def leg_chain_strikes(self, underlying: str, expiry: date, exchange: str = "NFO") -> tuple:
        """Return strike rows (dicts: strike_price, call_*/put_* ltp/oi/
        greeks) for the Add Leg dialog's strike picker -- the live
        tick-driven chain when ticks have arrived, else Market workspace's
        already-loaded REST snapshot, or () with a status message when
        neither has this underlying/expiry yet -- pure cache read, no
        broker call, safe to call directly, no worker."""
        result = self._ctx.provider.trading.leg_chain_strikes(
            self._ctx.session_id, underlying, exchange, expiry.strftime("%d-%b-%Y"),
        )
        if not result.success:
            self.status_message = result.message
            return ()
        return tuple(result.data)

    def load_expiry_chain(
        self,
        underlying: str,
        expiry: date,
        exchange: str = "NFO",
        *,
        on_done=None,
    ) -> None:
        """Fetch a fresh broker-REST option chain for underlying/expiry into
        the same session cache leg_chain_strikes() reads from -- used by the
        Add Leg dialog when the user picks an expiry Market workspace
        hasn't loaded yet (leg_chain_strikes() alone never calls the
        broker). Runs off the Qt UI thread via the same
        MarketWorkspaceService.initial_option_chain() path the Market tab
        uses; invokes on_done() (no args) once the fetch settles, success
        or failure, so the dialog can refresh its table."""
        expiry_str = expiry.strftime("%d-%b-%Y")

        def work():
            return self._ctx.provider.market.initial_option_chain(
                self._ctx.session_id, underlying, exchange=exchange, expiry_date=expiry_str,
            )

        def done(result):
            if not result or not result.success:
                self.status_message = result.message if result else "Option chain unavailable"
            if on_done:
                on_done()

        def err(msg: str):
            self.set_error(msg)
            if on_done:
                on_done()

        self._ctx.worker.run(work, done, err)

    def show_greeks_in_leg_picker(self) -> bool:
        """Whether the Add Leg dialog's strike picker should show Delta
        columns -- a user preference (Settings), off by default."""
        return self._ctx.provider.settings.get_preferences(self._ctx.session_id).show_greeks_in_leg_picker

    def save_new_strategy(self, name: str) -> None:
        """Persist the strategy currently being built and mark it active in
        Trading (create_strategy already does both in one call), in the
        background. A no-op with a friendly status message when there are no
        pending legs -- never calls the service with zero legs, since the
        engine would raise rather than return a soft failure for that."""
        legs = self._leg_builder.legs
        if not legs:
            self.status_message = "Add at least one leg before saving"
            return
        strategy = StrategyBuilder(name=name or "Custom Strategy").build()
        strategy = replace(
            strategy,
            metadata=replace(strategy.metadata, recognized_type=recognize_strategy(legs)),
            legs=legs,
        )
        self.busy = True

        def work():
            return self._ctx.provider.trading.create_strategy(self._ctx.session_id, strategy)

        def done(result):
            self.busy = False
            if result is None:
                return
            if not result.success:
                self.status_message = result.message
                return
            self._leg_builder = StrategyBuilder()
            self.pending_legs_changed.emit([])
            self.status_message = result.message

        def err(msg: str) -> None:
            self.busy = False
            self.set_error(msg)

        self._ctx.worker.run(work, done, err)

    def list_strategies(self) -> list[tuple[str, str]]:
        """Return (strategy_id, name) pairs for the Load dialog's picker
        list -- pure repository read, no broker call, safe to call
        directly, no worker."""
        result = self._ctx.provider.strategy.list_strategies(self._ctx.session_id)
        if not result.success:
            return []
        return [(s.strategy_id, s.metadata.name) for s in (result.data or [])]

    def load_strategy(self, strategy_id: str) -> None:
        """Load a saved strategy's legs into the builder currently being
        edited, and mark it active in both the Strategy and Trading
        workspaces (mirrors StrategyViewModel.open_strategy -- Trading's
        evaluate/optimize/paper-trade/margin actions only ever look at the
        Trading workspace's active entity_id, so it must be set here too)."""
        if not strategy_id:
            self.status_message = "No strategy selected"
            return
        strategy_result = self._ctx.provider.strategy.load_strategy(self._ctx.session_id, strategy_id)
        if not strategy_result.success:
            self.status_message = strategy_result.message
            return
        trading_result = self._ctx.provider.trading.load_strategy(self._ctx.session_id, strategy_id)
        if not trading_result.success:
            self.status_message = trading_result.message
            return
        strategy = trading_result.data
        self._leg_builder = StrategyBuilder().from_strategy(strategy)
        self.pending_legs_changed.emit(list(self._leg_builder.legs))
        self._strategy_name = strategy.metadata.name
        self.strategy_name_changed.emit(self._strategy_name)
        self.status_message = trading_result.message

    def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a saved strategy (used by the Open dialog's Delete button,
        both from the ribbon and the builder's own Load button). Returns
        whether the delete succeeded, so the dialog can drop the row from
        its list only on success."""
        result = self._ctx.provider.strategy.delete_strategy(self._ctx.session_id, strategy_id)
        self.status_message = result.message
        return result.success

    def generate_recommendation(self) -> None:
        """Trigger AI recommendation flow."""
        self._ctx.provider.navigation.navigate(
            self._ctx.session_id,
            WorkspaceType.AI,
        )
        self.status_message = "Navigate to AI workspace"

    def on_strategy_updated(self, payload: dict) -> None:
        """Handle strategy update event."""
        name = payload.get("strategy_id", "")
        self._strategy_name = name
        self.strategy_name_changed.emit(name)
