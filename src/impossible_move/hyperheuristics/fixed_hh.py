from __future__ import annotations

from typing import Sequence

from impossible_move.domain.models import BinPackingStateView
from impossible_move.optimization.contracts import HeuristicSelection, HyperHeuristic, LowLevelHeuristic


class FixedHyperHeuristic(HyperHeuristic):
    """Degenerate selector that always chooses one low-level heuristic.

    It is intentionally modelled through the same HyperHeuristic contract so a
    fixed policy can be compared with adaptive/random selection without adding
    special cases to the engine.
    """

    id = "fixed"
    display_name = "Fixed Strategy"

    def __init__(self, heuristic_id: str) -> None:
        if not heuristic_id.strip():
            raise ValueError("heuristic_id must be non-empty")
        self.heuristic_id = heuristic_id

    def select(
        self,
        state: BinPackingStateView,
        available_heuristics: Sequence[LowLevelHeuristic],
    ) -> HeuristicSelection:
        ids = [heuristic.id for heuristic in available_heuristics]
        if self.heuristic_id not in ids:
            raise ValueError(f"fixed heuristic {self.heuristic_id!r} is not available")
        return HeuristicSelection(
            heuristic_id=self.heuristic_id,
            scores={heuristic_id: (1.0 if heuristic_id == self.heuristic_id else 0.0) for heuristic_id in ids},
        )
