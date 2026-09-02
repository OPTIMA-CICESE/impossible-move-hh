from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from impossible_move.domain.exceptions import UnknownBinError
from impossible_move.domain.models import BinPackingInstance, BinPackingSolution, BinPackingState
from impossible_move.optimization.contracts import (
    HyperHeuristic,
    ItemOrderingStrategy,
    LowLevelHeuristic,
    PlacementEvaluation,
)
from impossible_move.trace.policy import TracePolicy
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
)

from .exceptions import (
    InvalidHeuristicSelectionError,
    InvalidOrderingError,
    InvalidPlacementError,
)
from .observer import DefaultStateObserver, StateObserver
from .recorder import TraceRecorder
from .result import RunResult


class BinPackingEngine:
    def __init__(self, observer: StateObserver | None = None) -> None:
        self.observer = observer or DefaultStateObserver()

    def solve(
        self,
        instance: BinPackingInstance,
        hyper_heuristic: HyperHeuristic,
        heuristics: Sequence[LowLevelHeuristic],
        ordering: ItemOrderingStrategy,
        *,
        run_id: str | None = None,
        trace_policy: TracePolicy = TracePolicy.FULL,
    ) -> RunResult:
        if not heuristics:
            raise ValueError("at least one low-level heuristic is required")

        heuristic_ids = [heuristic.id for heuristic in heuristics]
        if any(not heuristic_id.strip() for heuristic_id in heuristic_ids):
            raise ValueError("low-level heuristic ids must be non-empty")
        if len(heuristic_ids) != len(set(heuristic_ids)):
            raise ValueError("low-level heuristic ids must be unique")

        ordered_items = ordering.order(instance.items)
        self._validate_order(instance, ordered_items)
        state = BinPackingState.from_instance(instance, ordered_items)

        for heuristic in heuristics:
            heuristic.reset()
        hyper_heuristic.reset()

        actual_run_id = run_id or str(uuid4())
        trace_policy = TracePolicy(trace_policy)
        recorder = TraceRecorder(actual_run_id, trace_policy)
        placement_evaluation_count = 0
        recorder.append(
            RunStarted(
                sequence=0,
                step=0,
                run_id=actual_run_id,
                instance_id=instance.id,
                hyper_heuristic_id=hyper_heuristic.id,
                heuristic_ids=tuple(heuristic_ids),
                item_order=tuple(item.id for item in ordered_items),
                trace_policy=trace_policy.value,
            )
        )
        by_id = {heuristic.id: heuristic for heuristic in heuristics}

        while state.has_pending_items:
            if state.current_item is not None:
                raise RuntimeError("engine invariant violated: current item leaked between steps")
            item = state.begin_next_item()
            decision_step = state.step

            recorder.append(
                ItemSelected(
                    sequence=0,
                    step=decision_step,
                    item_id=item.id,
                    size=item.size,
                    remaining_items=len(state.unassigned_items),
                )
            )

            state_view = state.view()
            features = self.observer.observe(state_view)
            recorder.append(
                StateObserved(sequence=0, step=decision_step, features=features)
            )

            selection = hyper_heuristic.select(state_view, heuristics)
            try:
                heuristic = by_id[selection.heuristic_id]
            except KeyError as exc:
                raise InvalidHeuristicSelectionError(
                    f"hyper-heuristic selected unavailable heuristic {selection.heuristic_id!r}"
                ) from exc
            if selection.scores is not None:
                unknown_scores = set(selection.scores) - set(by_id)
                if unknown_scores:
                    raise InvalidHeuristicSelectionError(
                        f"hyper-heuristic emitted scores for unknown heuristics: {sorted(unknown_scores)!r}"
                    )
            unknown_reason_ids = {reason.heuristic_id for reason in selection.reasons} - set(by_id)
            if unknown_reason_ids:
                raise InvalidHeuristicSelectionError(
                    "hyper-heuristic emitted reasons for unknown heuristics: "
                    f"{sorted(unknown_reason_ids)!r}"
                )
            recorder.append(
                HeuristicSelected(
                    sequence=0,
                    step=decision_step,
                    heuristic_id=selection.heuristic_id,
                    scores=selection.scores,
                    reasons=selection.reasons,
                )
            )

            placement = heuristic.choose_placement(item, state_view)
            self._validate_evaluations(item, state, placement.evaluations)
            placement_evaluation_count += len(placement.evaluations)
            for evaluation in placement.evaluations:
                recorder.append(
                    PlacementEvaluated(
                        sequence=0,
                        step=decision_step,
                        bin_id=evaluation.bin_id,
                        feasible=evaluation.feasible,
                        remaining_before=evaluation.remaining_before,
                        remaining_after=evaluation.remaining_after,
                        score=evaluation.score,
                    )
                )

            self._validate_decision(item, state, placement.decision)
            recorder.append(
                PlacementSelected(
                    sequence=0,
                    step=decision_step,
                    bin_id=placement.decision.bin_id,
                    create_new_bin=placement.decision.create_new_bin,
                )
            )

            if placement.decision.create_new_bin:
                target = state.create_bin()
                recorder.append(
                    BinCreated(
                        sequence=0,
                        step=decision_step,
                        bin_id=target.id,
                        capacity=target.capacity,
                    )
                )
            else:
                assert placement.decision.bin_id is not None
                target = state.get_bin(placement.decision.bin_id)

            state.place_current_item(target.id)
            recorder.append(
                ItemPlaced(
                    sequence=0,
                    step=decision_step,
                    item_id=item.id,
                    bin_id=target.id,
                    used_capacity=target.used_capacity,
                    remaining_capacity=target.remaining_capacity,
                )
            )

        solution = BinPackingSolution.from_state(state)
        recorder.append(
            RunFinished(
                sequence=0,
                step=state.step,
                bins_used=solution.bins_used,
                total_capacity=solution.total_capacity,
                used_capacity=solution.total_size,
                unused_capacity=solution.unused_capacity,
                utilization=solution.utilization,
                lower_bound=solution.lower_bound,
                placement_evaluations=placement_evaluation_count,
            )
        )
        return RunResult(solution=solution, trace=recorder.build())

    @staticmethod
    def _validate_order(instance: BinPackingInstance, ordered_items: Sequence) -> None:
        expected = {item.id: item for item in instance.items}
        if len(ordered_items) != len(instance.items):
            raise InvalidOrderingError("ordering must return every instance item exactly once")
        ids = [item.id for item in ordered_items]
        if len(ids) != len(set(ids)) or set(ids) != set(expected):
            raise InvalidOrderingError("ordering must be a permutation of the instance items")
        if any(expected[item.id] != item for item in ordered_items):
            raise InvalidOrderingError("ordering returned an item inconsistent with the instance")

    @staticmethod
    def _validate_evaluations(
        item,
        state: BinPackingState,
        evaluations: Sequence[PlacementEvaluation],
    ) -> None:
        seen: set[int] = set()
        for evaluation in evaluations:
            if evaluation.bin_id in seen:
                raise InvalidPlacementError(
                    f"bin {evaluation.bin_id} was evaluated more than once"
                )
            seen.add(evaluation.bin_id)
            try:
                bin_ = state.get_bin(evaluation.bin_id)
            except UnknownBinError as exc:
                raise InvalidPlacementError(
                    f"evaluation references unknown bin {evaluation.bin_id}"
                ) from exc
            feasible = bin_.can_fit(item)
            remaining_after = bin_.remaining_capacity - item.size if feasible else None
            if (
                evaluation.feasible != feasible
                or evaluation.remaining_before != bin_.remaining_capacity
                or evaluation.remaining_after != remaining_after
            ):
                raise InvalidPlacementError(
                    f"evaluation for bin {bin_.id} is inconsistent with the current state"
                )

    @staticmethod
    def _validate_decision(item, state: BinPackingState, decision) -> None:
        if decision.create_new_bin:
            if item.size > state.instance.capacity:
                raise InvalidPlacementError("item cannot fit in a newly created bin")
            return
        assert decision.bin_id is not None
        try:
            bin_ = state.get_bin(decision.bin_id)
        except UnknownBinError as exc:
            raise InvalidPlacementError(
                f"placement references unknown bin {decision.bin_id}"
            ) from exc
        if not bin_.can_fit(item):
            raise InvalidPlacementError(
                f"item {item.id!r} does not fit in selected bin {bin_.id}"
            )
