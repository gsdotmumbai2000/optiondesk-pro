"""Trading workspace ViewModel."""

from dataclasses import replace

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
        self.save_command = RelayCommand(self.save, parent=self)
        self.load_command = RelayCommand(self.load, parent=self)
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
        """Recompute and publish payoff/Greeks for the active strategy by
        synchronously refreshing live analytics for its chain, in the
        background (the same live engines the tick pipeline uses, just run
        on demand rather than racing it)."""
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

    def save(self) -> None:
        """Save current strategy placeholder."""
        self.status_message = "Save: provide strategy from builder"

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

    def load(self) -> None:
        """Navigate to strategy workspace."""
        self._ctx.provider.navigation.navigate(
            self._ctx.session_id,
            WorkspaceType.STRATEGY,
        )
        self.status_message = "Open strategy loader"

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
