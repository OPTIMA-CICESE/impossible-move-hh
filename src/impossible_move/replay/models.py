from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from impossible_move.explainability import DecisionReason

from .actions import ReplayAction, ReplayMode
from .catalog import ReplayItemInfo


class ReplayStatus(str, Enum):
    EMPTY = "empty"
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass(frozen=True, slots=True)
class ReplayBinSnapshot:
    id: int
    capacity: int
    item_ids: tuple[str, ...]
    used_capacity: int
    remaining_capacity: int

    def __post_init__(self) -> None:
        if self.id < 0 or self.capacity <= 0:
            raise ValueError("replay bin id/capacity are invalid")
        if self.used_capacity < 0 or self.remaining_capacity < 0:
            raise ValueError("replay bin capacities must be non-negative")
        if self.used_capacity + self.remaining_capacity != self.capacity:
            raise ValueError("replay bin capacities must sum to capacity")


@dataclass(frozen=True, slots=True)
class ReplayPlacementEvaluation:
    bin_id: int
    feasible: bool
    remaining_before: int
    remaining_after: int | None
    score: float | None


@dataclass(frozen=True, slots=True)
class ReplayRunSummary:
    bins_used: int
    total_capacity: int
    used_capacity: int
    unused_capacity: int
    utilization: float
    lower_bound: int
    placement_evaluations: int = 0


@dataclass(frozen=True, slots=True)
class ReplaySnapshot:
    run_id: str | None
    instance_id: str | None
    hyper_heuristic_id: str | None
    heuristic_ids: tuple[str, ...]
    item_order: tuple[str, ...]
    remaining_item_ids: tuple[str, ...]
    status: ReplayStatus
    mode: ReplayMode
    speed: float
    cursor: int
    total_events: int
    current_step: int | None
    current_item: ReplayItemInfo | None
    bins: tuple[ReplayBinSnapshot, ...]
    features: Mapping[str, float]
    selected_heuristic_id: str | None
    heuristic_scores: Mapping[str, float]
    decision_reasons: tuple[DecisionReason, ...]
    heuristic_counts: Mapping[str, int]
    placement_evaluations: tuple[ReplayPlacementEvaluation, ...]
    selected_bin_id: int | None
    create_new_bin: bool
    summary: ReplayRunSummary | None
    trace_policy: str = "full"

    def __post_init__(self) -> None:
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))
        object.__setattr__(self, "heuristic_scores", MappingProxyType(dict(self.heuristic_scores)))
        object.__setattr__(self, "heuristic_counts", MappingProxyType(dict(self.heuristic_counts)))

    @property
    def progress(self) -> float:
        if self.total_events == 0 or self.cursor < 0:
            return 0.0
        return min(1.0, (self.cursor + 1) / self.total_events)


@dataclass(frozen=True, slots=True)
class ReplayFrame:
    action: ReplayAction
    snapshot: ReplaySnapshot
