from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from impossible_move.trace.events import HeuristicSelected, PlacementEvaluated, RunFinished
from impossible_move.trace.trace import RunTrace


@lru_cache(maxsize=None)
def bell_number(n: int) -> int:
    """Return Bell(n), the number of set partitions of n distinguishable items."""
    if n < 0:
        raise ValueError("n must be non-negative")
    row = [1]
    for i in range(1, n + 1):
        new_row = [row[-1]]
        for j in range(1, i + 1):
            new_row.append(new_row[-1] + row[j - 1])
        row = new_row
    return row[0]


def format_big_integer(value: int, *, significant_digits: int = 3) -> str:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value < 1_000_000:
        return f"{value:,}".replace(",", " ")
    digits = str(value)
    head = digits[:significant_digits]
    mantissa = head[0]
    if significant_digits > 1:
        mantissa += "." + head[1:]
    return f"{mantissa} × 10^{len(digits) - 1}"


@dataclass(frozen=True, slots=True)
class SearchSpaceEstimate:
    item_count: int
    heuristic_count: int
    decision_sequences: int
    theoretical_partitions: int
    decisions_observed: int = 0
    heuristic_options_scored: int = 0
    heuristic_options_not_selected: int = 0
    placement_evaluations: int = 0

    @classmethod
    def potential(cls, item_count: int, heuristic_count: int = 4) -> "SearchSpaceEstimate":
        if item_count < 0:
            raise ValueError("item_count must be non-negative")
        if heuristic_count <= 0:
            raise ValueError("heuristic_count must be positive")
        return cls(
            item_count=item_count,
            heuristic_count=heuristic_count,
            decision_sequences=heuristic_count**item_count,
            theoretical_partitions=bell_number(item_count),
        )

    def with_trace(self, trace: RunTrace) -> "SearchSpaceEstimate":
        decisions = sum(isinstance(event, HeuristicSelected) for event in trace.events)
        placements = sum(isinstance(event, PlacementEvaluated) for event in trace.events)
        finished = next((event for event in reversed(trace.events) if isinstance(event, RunFinished)), None)
        if finished is not None:
            placements = max(placements, int(finished.placement_evaluations))
        return SearchSpaceEstimate(
            item_count=self.item_count,
            heuristic_count=self.heuristic_count,
            decision_sequences=self.decision_sequences,
            theoretical_partitions=self.theoretical_partitions,
            decisions_observed=decisions,
            heuristic_options_scored=decisions * self.heuristic_count,
            heuristic_options_not_selected=decisions * max(0, self.heuristic_count - 1),
            placement_evaluations=placements,
        )

    def as_view(self) -> dict[str, object]:
        return {
            "itemCount": self.item_count,
            "heuristicCount": self.heuristic_count,
            "decisionSequences": str(self.decision_sequences),
            "decisionSequencesDisplay": format_big_integer(self.decision_sequences),
            "theoreticalPartitions": str(self.theoretical_partitions),
            "theoreticalPartitionsDisplay": format_big_integer(self.theoretical_partitions),
            "decisionsObserved": self.decisions_observed,
            "heuristicOptionsScored": self.heuristic_options_scored,
            "heuristicOptionsNotSelected": self.heuristic_options_not_selected,
            "placementEvaluations": self.placement_evaluations,
        }
