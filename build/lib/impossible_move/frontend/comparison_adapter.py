from __future__ import annotations

try:
    from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required for the GUI") from exc

from .comparison import ComparisonReplayController, comparison_view, move_explorer_view
from .i18n import DEFAULT_LANGUAGE


class QtComparisonAdapter(QObject):
    viewChanged = Signal()
    moveExplorerChanged = Signal()

    # GUI paints are intentionally capped. At high replay speeds several
    # decisions are advanced per paint instead of flooding QML with updates.
    MAX_VISUAL_FPS = 30
    BASE_DECISION_MS = 800.0

    def __init__(self, language_adapter=None, parent=None) -> None:
        super().__init__(parent)
        self._language_adapter = language_adapter
        self._controller: ComparisonReplayController | None = None
        self._view = {"active": False, "methods": [], "methodCount": 0}
        self._move_explorer = {"items": [], "groups": [], "itemCount": 0}
        self._move_explorer_active = False
        self._playing = False
        self._speed = 1.0
        self._explorer_frame_counter = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        if language_adapter is not None:
            language_adapter.languageChanged.connect(self._language_changed)

    @property
    def _language(self):
        return self._language_adapter.language if self._language_adapter is not None else DEFAULT_LANGUAGE

    def load(self, resolved) -> None:
        self._playing = False
        self._timer.stop()
        self._controller = ComparisonReplayController(resolved)
        self._move_explorer_active = False
        self._move_explorer = {"items": [], "groups": [], "itemCount": self._controller.total_decisions}
        self._refresh()
        self.moveExplorerChanged.emit()

    def clear(self) -> None:
        self._timer.stop()
        self._playing = False
        self._controller = None
        self._move_explorer_active = False
        self._move_explorer = {"items": [], "groups": [], "itemCount": 0}
        self._refresh()
        self.moveExplorerChanged.emit()

    def _language_changed(self) -> None:
        self._refresh()
        if self._move_explorer_active:
            self._refresh_move_explorer()

    def _refresh(self) -> None:
        self._view = comparison_view(self._controller, self._language) if self._controller else {"active": False, "methods": [], "methodCount": 0}
        self._view["playing"] = self._playing
        self._view["speed"] = self._speed
        self.viewChanged.emit()

    def _refresh_move_explorer(self) -> None:
        if self._controller is None:
            self._move_explorer = {"items": [], "groups": [], "itemCount": 0}
        else:
            self._move_explorer = move_explorer_view(self._controller, self._language)
        self.moveExplorerChanged.emit()

    def _timer_plan(self) -> tuple[int, int]:
        desired_ms = self.BASE_DECISION_MS / max(0.25, self._speed)
        minimum_ms = round(1000 / self.MAX_VISUAL_FPS)
        if desired_ms >= minimum_ms:
            return max(minimum_ms, round(desired_ms)), 1
        decisions = max(1, round(minimum_ms / desired_ms))
        return minimum_ms, decisions

    def _apply_timer_plan(self) -> None:
        interval, _ = self._timer_plan()
        self._timer.setInterval(interval)

    @Property("QVariantMap", notify=viewChanged)
    def view(self):
        return self._view

    @Property("QVariantMap", notify=moveExplorerChanged)
    def moveExplorer(self):
        return self._move_explorer

    @Slot()
    def prepareMoveExplorer(self):
        self._move_explorer_active = True
        self._refresh_move_explorer()

    @Slot()
    def releaseMoveExplorer(self):
        self._move_explorer_active = False
        # Keep only the small summary; 500 detailed rows no longer remain in
        # the Qt/QML property graph while the popup is closed.
        count = self._controller.total_decisions if self._controller else 0
        self._move_explorer = {"items": [], "groups": [], "itemCount": count}
        self.moveExplorerChanged.emit()

    @Slot()
    def togglePlayback(self):
        if not self._controller:
            return
        if self._controller.finished:
            self._controller.reset()
        self._playing = not self._playing
        if self._playing:
            self._apply_timer_plan()
            self._timer.start()
        else:
            self._timer.stop()
        self._refresh()

    @Slot()
    def nextDecision(self):
        if not self._controller:
            return
        self._timer.stop(); self._playing = False
        self._controller.advance_decision()
        self._refresh()
        if self._move_explorer_active:
            self._refresh_move_explorer()

    @Slot()
    def reset(self):
        if not self._controller:
            return
        self._timer.stop(); self._playing = False
        self._controller.reset(); self._refresh()
        if self._move_explorer_active:
            self._refresh_move_explorer()

    @Slot()
    def jumpToEnd(self):
        if not self._controller:
            return
        self._timer.stop(); self._playing = False
        self._controller.jump_to_end(); self._refresh()
        if self._move_explorer_active:
            self._refresh_move_explorer()

    @Slot(float)
    def setSpeed(self, speed):
        self._speed = max(0.25, float(speed))
        if self._timer.isActive():
            self._apply_timer_plan()
        self._refresh()

    @Slot()
    def _tick(self):
        if not self._controller or self._controller.finished:
            self._timer.stop(); self._playing = False; self._refresh(); return
        _, decisions_per_tick = self._timer_plan()
        for _ in range(decisions_per_tick):
            if self._controller.finished:
                break
            self._controller.advance_decision()
        if self._controller.finished:
            self._timer.stop(); self._playing = False
        self._refresh()
        if self._move_explorer_active:
            self._explorer_frame_counter += 1
            if self._explorer_frame_counter >= 6 or self._controller.finished:
                self._explorer_frame_counter = 0
                self._refresh_move_explorer()
