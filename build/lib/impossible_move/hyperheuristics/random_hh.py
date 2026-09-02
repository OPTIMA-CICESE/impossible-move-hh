from __future__ import annotations

from random import Random
from typing import Sequence

from impossible_move.domain.models import BinPackingStateView
from impossible_move.optimization.contracts import (
    HeuristicSelection,
    HyperHeuristic,
    LowLevelHeuristic,
)


class RandomHyperHeuristic(HyperHeuristic):
    id = "random"
    display_name = "Random Hyper-Heuristic"

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self._rng = Random(seed)

    def reset(self) -> None:
        self._rng = Random(self.seed)

    def select(
        self,
        state: BinPackingStateView,
        available_heuristics: Sequence[LowLevelHeuristic],
    ) -> HeuristicSelection:
        if not available_heuristics:
            raise ValueError("RandomHyperHeuristic requires at least one heuristic")
        selected = self._rng.choice(list(available_heuristics))
        probability = 1.0 / len(available_heuristics)
        return HeuristicSelection(
            heuristic_id=selected.id,
            scores={heuristic.id: probability for heuristic in available_heuristics},
        )
