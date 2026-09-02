from __future__ import annotations

import logging

try:
    from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without GUI extra
    raise RuntimeError(
        "PySide6 is required for the GUI. Install with: pip install -e '.[gui]'"
    ) from exc

from impossible_move.replay import ReplayController, ReplayFrame, ReplayMode, ReplayStatus

from .adaptive import recommended_speed, scale_for_catalog
from .i18n import DEFAULT_LANGUAGE, tr
from .presenter import action_to_transition, snapshot_to_view_model, trace_decision_history

logger = logging.getLogger(__name__)


class QtReplayAdapter(QObject):
    """Thin QObject/QTimer adapter around the UI-neutral ReplayController."""

    viewChanged = Signal()
    frameAdvanced = Signal("QVariantMap")

    def __init__(self, controller: ReplayController, language_adapter=None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._language_adapter = language_adapter
        self._last_action = ""
        self._interesting_info: dict = {}
        self._interesting_context: dict | None = None
        self._view: dict = {}
        self._history_cache: list[dict] = []
        self._timer = QTimer(self)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._on_timeout)
        self._unsubscribe = controller.subscribe(self._on_frame)
        if language_adapter is not None:
            language_adapter.languageChanged.connect(self._on_language_changed)
        self._prime()

    @property
    def _language(self) -> str:
        return self._language_adapter.language if self._language_adapter is not None else DEFAULT_LANGUAGE

    @Slot()
    def _on_language_changed(self) -> None:
        # Rebuild presentation strings only; trace cursor and solver state remain untouched.
        self._rebuild_history_cache()
        self._refresh()

    def _rebuild_history_cache(self) -> None:
        trace = self._controller.trace
        self._history_cache = (
            trace_decision_history(trace, self._controller.catalog, self._language)
            if trace is not None else []
        )

    def _attach_history(self) -> None:
        # Full trace histories are useful for inspection but expensive to push
        # through Qt on every animation frame. During automatic playback the
        # distribution counters remain visible; detailed history is attached
        # again as soon as playback pauses or finishes.
        if self._controller.status is ReplayStatus.PLAYING:
            self._view["decisionHistory"] = []
            self._view["heuristicHistories"] = []
            return
        limit = int(self._view.get("decisionCount", 0))
        rows = self._history_cache[:max(0, limit)]
        ids = ("first_fit", "best_fit", "worst_fit", "next_fit")
        total = len(rows)
        self._view["decisionHistory"] = rows
        self._view["heuristicHistories"] = [
            {
                "id": heuristic_id,
                "label": next((r["heuristicLabel"] for r in rows if r["heuristic_id"] == heuristic_id), heuristic_id.replace("_", " ").title()),
                "count": sum(1 for r in rows if r["heuristic_id"] == heuristic_id),
                "fraction": (sum(1 for r in rows if r["heuristic_id"] == heuristic_id) / total) if total else 0.0,
                "decisions": [r for r in rows if r["heuristic_id"] == heuristic_id],
            }
            for heuristic_id in ids
        ]

    def _prime(self) -> None:
        trace = self._controller.trace
        if trace is not None and trace.events:
            self._controller.seek_sequence(0)
        self._rebuild_history_cache()
        self._refresh()

    def _refresh(self) -> None:
        self._view = snapshot_to_view_model(
            self._controller.snapshot,
            self._controller.catalog,
            last_action=self._last_action,
            language=self._language,
            interesting_info=self._interesting_info,
        )
        self._attach_history()
        self.viewChanged.emit()

    def _interesting_feedback(self, frame: ReplayFrame) -> dict:
        context = self._interesting_context or {}
        start_step = int(context.get("fromStep", -1))
        previous_heuristic = str(context.get("previousHeuristic", ""))
        previous_bins = int(context.get("binCount", 0))
        target_step = int(frame.snapshot.current_step if frame.snapshot.current_step is not None else start_step)
        skipped = max(0, target_step - start_step - 1)
        action_type = frame.action.type.value
        reason_key = ""
        if len(frame.snapshot.bins) > previous_bins:
            reason_key = "relevant_new_bin"
        elif action_type == "run_finished":
            reason_key = "relevant_finished"
        else:
            rule_ids = {reason.rule_id for reason in frame.snapshot.decision_reasons}
            if "exact_fit" in rule_ids:
                reason_key = "relevant_exact_fit"
            elif "no_existing_fit" in rule_ids:
                reason_key = "relevant_no_fit"
            elif frame.snapshot.selected_heuristic_id and frame.snapshot.selected_heuristic_id != previous_heuristic:
                reason_key = "relevant_strategy_change"
        if not reason_key:
            reason_key = "relevant_strategy_change"
        return {
            "visible": True,
            "skippedDecisions": skipped,
            "reasonKey": reason_key,
            "reason": tr(reason_key, self._language),
            "step": target_step,
        }

    def _on_frame(self, frame: ReplayFrame) -> None:
        transition = action_to_transition(
            frame.action,
            frame.snapshot,
            self._controller.catalog,
            language=self._language,
        )
        self.frameAdvanced.emit(transition)

        self._last_action = frame.action.type.value
        if self._interesting_context is not None:
            self._interesting_info = self._interesting_feedback(frame)
        self._view = snapshot_to_view_model(
            frame.snapshot,
            self._controller.catalog,
            last_action=self._last_action,
            language=self._language,
            interesting_info=self._interesting_info,
        )
        self._attach_history()
        if frame.snapshot.status is ReplayStatus.FINISHED:
            self._timer.stop()
        self.viewChanged.emit()

    def _clear_interesting(self) -> None:
        self._interesting_info = {}
        self._interesting_context = None

    @Slot()
    def _on_timeout(self) -> None:
        frame = self._controller.tick()
        if frame is None and self._controller.status is not ReplayStatus.PLAYING:
            self._timer.stop()
        elif frame is None and self._controller.status is ReplayStatus.FINISHED:
            self._timer.stop()
            self._refresh()

    @Property("QVariantMap", notify=viewChanged)
    def view(self) -> dict:
        return self._view

    @Property(str, notify=viewChanged)
    def status(self) -> str:
        return self._controller.status.value

    @Property(bool, notify=viewChanged)
    def playing(self) -> bool:
        return self._controller.status is ReplayStatus.PLAYING

    @Property(float, notify=viewChanged)
    def speed(self) -> float:
        return self._controller.speed

    @Property(str, notify=viewChanged)
    def mode(self) -> str:
        return self._controller.mode.value

    def load_run(self, trace, catalog) -> None:
        logger.info("Replay run loaded | run_id=%s | events=%s", getattr(trace, "run_id", ""), len(trace.events))
        self._timer.stop()
        self._controller.load_trace(trace, catalog=catalog)
        self._controller.set_speed(recommended_speed(scale_for_catalog(catalog)))
        self._rebuild_history_cache()
        self._last_action = ""
        self._clear_interesting()
        self._prime()

    @Slot()
    def togglePlayback(self) -> None:
        self._clear_interesting()
        logger.info("Replay toggle | current_status=%s", self._controller.status.value)
        if self._controller.status is ReplayStatus.PLAYING:
            self._controller.pause()
            self._timer.stop()
        else:
            if self._controller.status is ReplayStatus.FINISHED:
                self._controller.reset()
                self._prime()
            self._controller.play()
            self._timer.setInterval(self._controller.interval_ms)
            self._timer.start()
        self._refresh()

    @Slot()
    def reset(self) -> None:
        logger.info("Replay reset")
        self._timer.stop()
        self._controller.reset()
        self._last_action = ""
        self._clear_interesting()
        self._prime()

    @Slot()
    def step(self) -> None:
        self._timer.stop()
        self._controller.pause()
        self._clear_interesting()
        self._controller.advance()
        self._refresh()

    @Slot()
    def nextDecision(self) -> None:
        self._timer.stop()
        self._controller.pause()
        self._clear_interesting()
        self._controller.advance_decision()
        self._refresh()

    @Slot()
    def nextInteresting(self) -> None:
        logger.info("Replay next relevant decision | from_step=%s", self._controller.snapshot.current_step)
        self._timer.stop()
        self._controller.pause()
        snapshot = self._controller.snapshot
        self._interesting_info = {}
        self._interesting_context = {
            "fromStep": snapshot.current_step if snapshot.current_step is not None else -1,
            "previousHeuristic": snapshot.selected_heuristic_id or "",
            "binCount": len(snapshot.bins),
        }
        frame = self._controller.advance_interesting()
        self._interesting_context = None
        if frame is None:
            self._interesting_info = {}
        self._refresh()

    @Slot()
    def jumpToEnd(self) -> None:
        logger.info("Replay jump to end")
        self._timer.stop()
        self._controller.pause()
        self._clear_interesting()
        self._controller.jump_to_end()
        self._refresh()

    @Slot(float)
    def setSpeed(self, multiplier: float) -> None:
        logger.info("Replay speed changed | speed=%sx", multiplier)
        self._controller.set_speed(multiplier)
        if self._timer.isActive():
            self._timer.setInterval(self._controller.interval_ms)
        self._refresh()

    @Slot(str)
    def setMode(self, value: str) -> None:
        logger.info("Replay mode changed | mode=%s", value)
        self._controller.set_mode(ReplayMode(value))
        self._refresh()
