from __future__ import annotations

from impossible_move.domain.models import BinPackingStateView, BinSnapshot, Item
from impossible_move.optimization.contracts import (
    LowLevelHeuristic,
    PlacementDecision,
    PlacementEvaluation,
    PlacementResult,
)


def _evaluate(item: Item, bin_: BinSnapshot, *, score: float | None = None) -> PlacementEvaluation:
    feasible = bin_.can_fit(item)
    return PlacementEvaluation(
        bin_id=bin_.id,
        feasible=feasible,
        remaining_before=bin_.remaining_capacity,
        remaining_after=bin_.remaining_capacity - item.size if feasible else None,
        score=score if feasible else None,
    )


class FirstFit(LowLevelHeuristic):
    id = "first_fit"
    display_name = "First Fit"

    def choose_placement(self, item: Item, state: BinPackingStateView) -> PlacementResult:
        evaluations: list[PlacementEvaluation] = []
        for bin_ in state.bins:
            evaluation = _evaluate(item, bin_)
            evaluations.append(evaluation)
            if evaluation.feasible:
                return PlacementResult(
                    decision=PlacementDecision(bin_id=bin_.id),
                    evaluations=tuple(evaluations),
                )
        return PlacementResult(
            decision=PlacementDecision(create_new_bin=True),
            evaluations=tuple(evaluations),
        )


class BestFit(LowLevelHeuristic):
    id = "best_fit"
    display_name = "Best Fit"

    def choose_placement(self, item: Item, state: BinPackingStateView) -> PlacementResult:
        evaluations: list[PlacementEvaluation] = []
        feasible_bins: list[tuple[int, int]] = []
        for bin_ in state.bins:
            remaining_after = bin_.remaining_capacity - item.size
            feasible = remaining_after >= 0
            evaluation = _evaluate(
                item,
                bin_,
                score=float(remaining_after) if feasible else None,
            )
            evaluations.append(evaluation)
            if feasible:
                feasible_bins.append((remaining_after, bin_.id))

        if not feasible_bins:
            return PlacementResult(
                decision=PlacementDecision(create_new_bin=True),
                evaluations=tuple(evaluations),
            )
        _, bin_id = min(feasible_bins)
        return PlacementResult(
            decision=PlacementDecision(bin_id=bin_id),
            evaluations=tuple(evaluations),
        )


class WorstFit(LowLevelHeuristic):
    id = "worst_fit"
    display_name = "Worst Fit"

    def choose_placement(self, item: Item, state: BinPackingStateView) -> PlacementResult:
        evaluations: list[PlacementEvaluation] = []
        feasible_bins: list[tuple[int, int]] = []
        for bin_ in state.bins:
            remaining_after = bin_.remaining_capacity - item.size
            feasible = remaining_after >= 0
            evaluation = _evaluate(
                item,
                bin_,
                score=float(remaining_after) if feasible else None,
            )
            evaluations.append(evaluation)
            if feasible:
                feasible_bins.append((remaining_after, -bin_.id))

        if not feasible_bins:
            return PlacementResult(
                decision=PlacementDecision(create_new_bin=True),
                evaluations=tuple(evaluations),
            )
        _, negative_bin_id = max(feasible_bins)
        return PlacementResult(
            decision=PlacementDecision(bin_id=-negative_bin_id),
            evaluations=tuple(evaluations),
        )


class NextFit(LowLevelHeuristic):
    id = "next_fit"
    display_name = "Next Fit"

    def choose_placement(self, item: Item, state: BinPackingStateView) -> PlacementResult:
        if not state.bins:
            return PlacementResult(decision=PlacementDecision(create_new_bin=True))
        last_bin = state.bins[-1]
        evaluation = _evaluate(item, last_bin)
        if evaluation.feasible:
            decision = PlacementDecision(bin_id=last_bin.id)
        else:
            decision = PlacementDecision(create_new_bin=True)
        return PlacementResult(decision=decision, evaluations=(evaluation,))
