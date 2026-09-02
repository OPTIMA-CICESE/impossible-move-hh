from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Callable

from impossible_move.explainability import DecisionReason
from impossible_move.trace.events import (
    BinCreated,
    HeuristicSelected,
    ItemPlaced,
    ItemSelected,
    PlacementEvaluated,
    PlacementSelected,
    RunFinished,
    RunStarted,
    StateObserved,
    TraceEventType,
)
from impossible_move.trace.trace import RunTrace

from .actions import ReplayMode, action_from_event, is_visible
from .catalog import ReplayCatalog, ReplayItemInfo
from .exceptions import ReplayConsistencyError
from .models import (
    ReplayBinSnapshot,
    ReplayFrame,
    ReplayPlacementEvaluation,
    ReplayRunSummary,
    ReplaySnapshot,
    ReplayStatus,
)

ReplaySubscriber = Callable[[ReplayFrame], None]


class _MutableReplayBin:
    __slots__ = ("id", "capacity", "item_ids", "used_capacity", "remaining_capacity")

    def __init__(self, bin_id: int, capacity: int) -> None:
        self.id = bin_id
        self.capacity = capacity
        self.item_ids: list[str] = []
        self.used_capacity = 0
        self.remaining_capacity = capacity

    def snapshot(self) -> ReplayBinSnapshot:
        return ReplayBinSnapshot(
            id=self.id,
            capacity=self.capacity,
            item_ids=tuple(self.item_ids),
            used_capacity=self.used_capacity,
            remaining_capacity=self.remaining_capacity,
        )


class ReplayController:
    """Pure-Python trace player.

    Time is deliberately external.  ``play()`` changes state and ``tick()``
    advances one visible action; a future Qt adapter can call ``tick()`` from a
    QTimer using ``interval_ms``.  Manual stepping works without Qt or threads.
    """

    def __init__(
        self,
        trace: RunTrace | None = None,
        *,
        catalog: ReplayCatalog | None = None,
        mode: ReplayMode = ReplayMode.DETAILED,
        speed: float = 1.0,
        base_interval_ms: int = 800,
    ) -> None:
        if base_interval_ms <= 0:
            raise ValueError("base_interval_ms must be positive")
        self._base_interval_ms = base_interval_ms
        self._mode = ReplayMode(mode)
        self._speed = 1.0
        self.set_speed(speed)
        self._subscribers: list[ReplaySubscriber] = []
        self._trace: RunTrace | None = None
        self._catalog: ReplayCatalog | None = None
        self._clear_runtime_state()
        if trace is not None:
            self.load_trace(trace, catalog=catalog)
        elif catalog is not None:
            raise ValueError("catalog cannot be supplied without a trace")

    @property
    def trace(self) -> RunTrace | None:
        return self._trace

    @property
    def catalog(self) -> ReplayCatalog | None:
        return self._catalog

    @property
    def mode(self) -> ReplayMode:
        return self._mode

    @property
    def status(self) -> ReplayStatus:
        return self._status

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def interval_ms(self) -> int:
        return max(1, round(self._base_interval_ms / self._speed))

    @property
    def snapshot(self) -> ReplaySnapshot:
        return self._snapshot()

    def load_trace(self, trace: RunTrace, *, catalog: ReplayCatalog | None = None) -> None:
        if catalog is not None:
            start = next((event for event in trace.events if isinstance(event, RunStarted)), None)
            if start is not None and catalog.instance_id != start.instance_id:
                raise ValueError(
                    f"catalog instance {catalog.instance_id!r} does not match "
                    f"trace instance {start.instance_id!r}"
                )
        self._trace = trace
        self._catalog = catalog
        self.reset()

    def set_mode(self, mode: ReplayMode) -> None:
        self._mode = ReplayMode(mode)

    def set_speed(self, multiplier: float) -> None:
        if not isfinite(multiplier) or multiplier <= 0:
            raise ValueError("speed multiplier must be finite and positive")
        self._speed = float(multiplier)

    def subscribe(self, callback: ReplaySubscriber) -> Callable[[], None]:
        if callback in self._subscribers:
            raise ValueError("callback is already subscribed")
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            self.unsubscribe(callback)

        return unsubscribe

    def unsubscribe(self, callback: ReplaySubscriber) -> None:
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass

    def reset(self) -> None:
        self._clear_runtime_state()
        self._status = ReplayStatus.READY if self._trace is not None else ReplayStatus.EMPTY

    def play(self) -> None:
        self._require_trace()
        if self._status is ReplayStatus.FINISHED:
            return
        self._status = ReplayStatus.PLAYING

    def pause(self) -> None:
        if self._status is ReplayStatus.PLAYING:
            self._status = ReplayStatus.PAUSED

    def tick(self) -> ReplayFrame | None:
        if self._status is not ReplayStatus.PLAYING:
            return None
        return self.advance()

    def advance(self) -> ReplayFrame | None:
        """Advance through hidden events and return the next visible frame."""
        trace = self._require_trace()
        if self._status is ReplayStatus.FINISHED:
            return None
        while self._cursor + 1 < len(trace.events):
            event = trace.events[self._cursor + 1]
            self._apply(event)
            self._cursor = event.sequence
            action = action_from_event(event)
            if self._cursor == len(trace.events) - 1:
                self._status = ReplayStatus.FINISHED
            if is_visible(action.type, self._mode):
                frame = ReplayFrame(action=action, snapshot=self._snapshot())
                self._emit(frame)
                return frame
        self._status = ReplayStatus.FINISHED
        return None

    def advance_decision(self) -> ReplayFrame | None:
        """Advance to the end of the next item-placement decision.

        The boundary is ``ItemPlaced`` (or ``RunFinished`` for an empty run),
        independent of the current visual replay mode.
        """
        trace = self._require_trace()
        if self._status is ReplayStatus.FINISHED:
            return None
        last_event: TraceEventType | None = None
        while self._cursor + 1 < len(trace.events):
            event = trace.events[self._cursor + 1]
            self._apply(event)
            self._cursor = event.sequence
            last_event = event
            if isinstance(event, (ItemPlaced, RunFinished)):
                break
        if last_event is None:
            self._status = ReplayStatus.FINISHED
            return None
        if self._cursor == len(trace.events) - 1:
            self._status = ReplayStatus.FINISHED
        frame = ReplayFrame(action=action_from_event(last_event), snapshot=self._snapshot())
        self._emit(frame)
        return frame


    def advance_interesting(self) -> ReplayFrame | None:
        """Advance through routine decisions to the next notable *complete* decision.

        A decision is notable when it opens a new bin, changes the selected
        low-level heuristic, or activates an exact-fit/no-fit rule.  Unlike a
        single event step, this method always continues through ``ItemPlaced``
        so the UI lands on a complete, understandable decision state.
        """
        trace = self._require_trace()
        if self._status is ReplayStatus.FINISHED:
            return None

        previous_heuristic = self._selected_heuristic_id
        decision_notable = False
        target: TraceEventType | None = None

        while self._cursor + 1 < len(trace.events):
            event = trace.events[self._cursor + 1]
            self._apply(event)
            self._cursor = event.sequence

            if isinstance(event, BinCreated):
                # Opening the very first truck is unavoidable and therefore not
                # pedagogically interesting by itself. Later openings are.
                if len(self._bins) > 1:
                    decision_notable = True
            elif isinstance(event, HeuristicSelected):
                rule_ids = {reason.rule_id for reason in event.reasons}
                if previous_heuristic is not None and event.heuristic_id != previous_heuristic:
                    decision_notable = True
                if "exact_fit" in rule_ids:
                    decision_notable = True
                if "no_existing_fit" in rule_ids and len(self._bins) > 0:
                    decision_notable = True
                previous_heuristic = event.heuristic_id
            elif isinstance(event, ItemPlaced):
                if decision_notable:
                    target = event
                    break
                decision_notable = False
            elif isinstance(event, RunFinished):
                target = event
                break

        if target is None:
            self._status = ReplayStatus.FINISHED
            return None
        if self._cursor == len(trace.events) - 1:
            self._status = ReplayStatus.FINISHED
        frame = ReplayFrame(action=action_from_event(target), snapshot=self._snapshot())
        self._emit(frame)
        return frame

    def seek_sequence(self, sequence: int) -> ReplayFrame | None:
        trace = self._require_trace()
        if sequence < -1 or sequence >= len(trace.events):
            raise IndexError("sequence is outside the trace")
        self.reset()
        if sequence == -1:
            return None
        target: TraceEventType | None = None
        for event in trace.events[: sequence + 1]:
            self._apply(event)
            self._cursor = event.sequence
            target = event
        assert target is not None
        if self._cursor == len(trace.events) - 1:
            self._status = ReplayStatus.FINISHED
        frame = ReplayFrame(action=action_from_event(target), snapshot=self._snapshot())
        self._emit(frame)
        return frame

    def seek_step(self, step: int) -> ReplayFrame | None:
        """Seek to the final event belonging to ``step``.

        This is useful for a scrubber indexed by optimization decisions.  If a
        run-finished event uses the requested step, it is included.
        """
        if step < 0:
            raise ValueError("step must be non-negative")
        trace = self._require_trace()
        matches = [event.sequence for event in trace.events if event.step == step]
        if not matches:
            raise IndexError(f"step {step} does not exist in the trace")
        return self.seek_sequence(max(matches))

    def jump_to_end(self) -> ReplayFrame | None:
        trace = self._require_trace()
        if not trace.events:
            self._status = ReplayStatus.FINISHED
            return None
        return self.seek_sequence(len(trace.events) - 1)

    def _require_trace(self) -> RunTrace:
        if self._trace is None:
            raise RuntimeError("no trace is loaded")
        return self._trace

    def _clear_runtime_state(self) -> None:
        self._status = ReplayStatus.EMPTY
        self._cursor = -1
        self._run_id: str | None = None
        self._instance_id: str | None = None
        self._hyper_heuristic_id: str | None = None
        self._heuristic_ids: tuple[str, ...] = ()
        self._item_order: tuple[str, ...] = ()
        self._trace_policy = "full"
        self._remaining_item_ids: list[str] = []
        self._current_step: int | None = None
        self._current_item: ReplayItemInfo | None = None
        self._bins: dict[int, _MutableReplayBin] = {}
        self._features: dict[str, float] = {}
        self._selected_heuristic_id: str | None = None
        self._heuristic_scores: dict[str, float] = {}
        self._decision_reasons: tuple[DecisionReason, ...] = ()
        self._heuristic_counts: Counter[str] = Counter()
        self._placement_evaluations: list[ReplayPlacementEvaluation] = []
        self._selected_bin_id: int | None = None
        self._create_new_bin = False
        self._summary: ReplayRunSummary | None = None
        self._item_sizes: dict[str, int] = {}

    def _resolve_item(self, item_id: str, size: int) -> ReplayItemInfo:
        if self._catalog is not None:
            try:
                info = self._catalog.items[item_id]
            except KeyError as exc:
                raise ReplayConsistencyError(
                    f"trace references item {item_id!r} missing from replay catalog"
                ) from exc
            if info.size != size:
                raise ReplayConsistencyError(
                    f"catalog size for {item_id!r} ({info.size}) differs from trace ({size})"
                )
            return info
        return ReplayItemInfo(id=item_id, display_name=item_id, size=size)

    def _apply(self, event: TraceEventType) -> None:
        self._current_step = event.step
        if isinstance(event, RunStarted):
            if event.sequence != 0:
                raise ReplayConsistencyError("RunStarted must be the first event")
            self._run_id = event.run_id
            self._instance_id = event.instance_id
            self._hyper_heuristic_id = event.hyper_heuristic_id
            self._heuristic_ids = event.heuristic_ids
            if len(event.item_order) != len(set(event.item_order)):
                raise ReplayConsistencyError("RunStarted item_order contains duplicate item ids")
            self._item_order = event.item_order
            self._trace_policy = event.trace_policy
            self._remaining_item_ids = list(event.item_order)
            return

        if self._run_id is None:
            raise ReplayConsistencyError("trace event occurred before RunStarted")

        if isinstance(event, ItemSelected):
            if self._current_item is not None:
                raise ReplayConsistencyError("another item was selected before placing the current item")
            if not self._remaining_item_ids:
                raise ReplayConsistencyError("ItemSelected occurred after the declared item order was exhausted")
            expected_item_id = self._remaining_item_ids[0]
            if event.item_id != expected_item_id:
                raise ReplayConsistencyError(
                    f"selected item {event.item_id!r} does not match declared order item {expected_item_id!r}"
                )
            self._remaining_item_ids.pop(0)
            if event.remaining_items != len(self._remaining_item_ids):
                raise ReplayConsistencyError(
                    "ItemSelected.remaining_items does not match the declared item order"
                )
            known = self._item_sizes.get(event.item_id)
            if known is not None and known != event.size:
                raise ReplayConsistencyError(f"item {event.item_id!r} changed size during replay")
            self._item_sizes[event.item_id] = event.size
            self._current_item = self._resolve_item(event.item_id, event.size)
            self._features = {}
            self._selected_heuristic_id = None
            self._heuristic_scores = {}
            self._decision_reasons = ()
            self._placement_evaluations = []
            self._selected_bin_id = None
            self._create_new_bin = False
            return

        if isinstance(event, StateObserved):
            self._features = dict(event.features)
            return

        if isinstance(event, HeuristicSelected):
            if event.heuristic_id not in self._heuristic_ids:
                raise ReplayConsistencyError(
                    f"selected heuristic {event.heuristic_id!r} was not declared by RunStarted"
                )
            self._selected_heuristic_id = event.heuristic_id
            self._heuristic_scores = dict(event.scores or {})
            self._decision_reasons = event.reasons
            self._heuristic_counts[event.heuristic_id] += 1
            return

        if isinstance(event, PlacementEvaluated):
            if event.bin_id not in self._bins:
                raise ReplayConsistencyError(
                    f"placement evaluation references unknown bin {event.bin_id}"
                )
            self._placement_evaluations.append(
                ReplayPlacementEvaluation(
                    bin_id=event.bin_id,
                    feasible=event.feasible,
                    remaining_before=event.remaining_before,
                    remaining_after=event.remaining_after,
                    score=event.score,
                )
            )
            return

        if isinstance(event, PlacementSelected):
            if self._current_item is None:
                raise ReplayConsistencyError("placement selected without a current item")
            if not event.create_new_bin and event.bin_id not in self._bins:
                raise ReplayConsistencyError(
                    f"placement selected unknown bin {event.bin_id}"
                )
            self._selected_bin_id = event.bin_id
            self._create_new_bin = event.create_new_bin
            return

        if isinstance(event, BinCreated):
            if event.bin_id in self._bins:
                raise ReplayConsistencyError(f"bin {event.bin_id} was created more than once")
            self._bins[event.bin_id] = _MutableReplayBin(event.bin_id, event.capacity)
            return

        if isinstance(event, ItemPlaced):
            if self._current_item is None:
                raise ReplayConsistencyError("ItemPlaced occurred without ItemSelected")
            if event.item_id != self._current_item.id:
                raise ReplayConsistencyError(
                    f"placed item {event.item_id!r} differs from current item {self._current_item.id!r}"
                )
            try:
                bin_ = self._bins[event.bin_id]
            except KeyError as exc:
                raise ReplayConsistencyError(
                    f"ItemPlaced references unknown bin {event.bin_id}"
                ) from exc
            expected_used = bin_.used_capacity + self._current_item.size
            expected_remaining = bin_.capacity - expected_used
            if event.used_capacity != expected_used or event.remaining_capacity != expected_remaining:
                raise ReplayConsistencyError(
                    f"ItemPlaced capacities for bin {event.bin_id} do not match reconstructed state"
                )
            if event.item_id in (item for current in self._bins.values() for item in current.item_ids):
                raise ReplayConsistencyError(f"item {event.item_id!r} was placed more than once")
            bin_.item_ids.append(event.item_id)
            bin_.used_capacity = event.used_capacity
            bin_.remaining_capacity = event.remaining_capacity
            self._selected_bin_id = event.bin_id
            self._current_item = None
            return

        if isinstance(event, RunFinished):
            if self._current_item is not None or self._remaining_item_ids:
                raise ReplayConsistencyError("RunFinished occurred before all declared items were placed")
            bins_used = len(self._bins)
            total_capacity = sum(bin_.capacity for bin_ in self._bins.values())
            used_capacity = sum(bin_.used_capacity for bin_ in self._bins.values())
            unused_capacity = sum(bin_.remaining_capacity for bin_ in self._bins.values())
            if (
                event.bins_used != bins_used
                or event.total_capacity != total_capacity
                or event.used_capacity != used_capacity
                or event.unused_capacity != unused_capacity
            ):
                raise ReplayConsistencyError("RunFinished does not match reconstructed bin state")
            self._summary = ReplayRunSummary(
                bins_used=event.bins_used,
                total_capacity=event.total_capacity,
                used_capacity=event.used_capacity,
                unused_capacity=event.unused_capacity,
                utilization=event.utilization,
                lower_bound=event.lower_bound,
                placement_evaluations=event.placement_evaluations,
            )
            return

        raise TypeError(f"unsupported trace event {type(event).__name__}")

    def _snapshot(self) -> ReplaySnapshot:
        total_events = len(self._trace.events) if self._trace is not None else 0
        return ReplaySnapshot(
            run_id=self._run_id,
            instance_id=self._instance_id,
            hyper_heuristic_id=self._hyper_heuristic_id,
            heuristic_ids=self._heuristic_ids,
            item_order=self._item_order,
            trace_policy=self._trace_policy,
            remaining_item_ids=tuple(self._remaining_item_ids),
            status=self._status,
            mode=self._mode,
            speed=self._speed,
            cursor=self._cursor,
            total_events=total_events,
            current_step=self._current_step,
            current_item=self._current_item,
            bins=tuple(self._bins[key].snapshot() for key in sorted(self._bins)),
            features=self._features,
            selected_heuristic_id=self._selected_heuristic_id,
            heuristic_scores=self._heuristic_scores,
            decision_reasons=self._decision_reasons,
            heuristic_counts=self._heuristic_counts,
            placement_evaluations=tuple(self._placement_evaluations),
            selected_bin_id=self._selected_bin_id,
            create_new_bin=self._create_new_bin,
            summary=self._summary,
        )

    def _emit(self, frame: ReplayFrame) -> None:
        for callback in tuple(self._subscribers):
            callback(frame)
