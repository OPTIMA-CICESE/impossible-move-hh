from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from time import time_ns
from types import MappingProxyType
from typing import Mapping

from impossible_move.explainability import DecisionReason


def _nonempty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceEvent:
    sequence: int
    step: int
    timestamp_ns: int = field(default_factory=time_ns)

    def __post_init__(self) -> None:
        if self.sequence < 0 or self.step < 0:
            raise ValueError("event sequence and step must be non-negative")
        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must be non-negative")

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True, slots=True, kw_only=True)
class RunStarted(TraceEvent):
    run_id: str
    instance_id: str
    hyper_heuristic_id: str
    heuristic_ids: tuple[str, ...]
    item_order: tuple[str, ...]
    trace_policy: str = "full"

    def __post_init__(self) -> None:
        super(RunStarted, self).__post_init__()
        _nonempty(self.run_id, "run_id")
        _nonempty(self.instance_id, "instance_id")
        _nonempty(self.hyper_heuristic_id, "hyper_heuristic_id")
        if len(self.heuristic_ids) != len(set(self.heuristic_ids)):
            raise ValueError("heuristic_ids must be unique")
        if self.trace_policy not in {"full", "standard", "compact"}:
            raise ValueError("trace_policy must be full, standard or compact")


@dataclass(frozen=True, slots=True, kw_only=True)
class ItemSelected(TraceEvent):
    item_id: str
    size: int
    remaining_items: int

    def __post_init__(self) -> None:
        super(ItemSelected, self).__post_init__()
        _nonempty(self.item_id, "item_id")
        if self.size <= 0 or self.remaining_items < 0:
            raise ValueError("item size must be positive and remaining_items non-negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateObserved(TraceEvent):
    features: Mapping[str, float]

    def __post_init__(self) -> None:
        super(StateObserved, self).__post_init__()
        copied = dict(self.features)
        if any(not key.strip() for key in copied):
            raise ValueError("feature names must be non-empty")
        if any(not isfinite(value) for value in copied.values()):
            raise ValueError("state features must be finite")
        object.__setattr__(self, "features", MappingProxyType(copied))


@dataclass(frozen=True, slots=True, kw_only=True)
class HeuristicSelected(TraceEvent):
    heuristic_id: str
    scores: Mapping[str, float] | None = None
    reasons: tuple[DecisionReason, ...] = ()

    def __post_init__(self) -> None:
        super(HeuristicSelected, self).__post_init__()
        _nonempty(self.heuristic_id, "heuristic_id")
        if self.scores is not None:
            copied = dict(self.scores)
            if any(not key.strip() for key in copied):
                raise ValueError("score heuristic ids must be non-empty")
            if any(not isfinite(value) for value in copied.values()):
                raise ValueError("heuristic scores must be finite")
            object.__setattr__(self, "scores", MappingProxyType(copied))
        if any(not isinstance(reason, DecisionReason) for reason in self.reasons):
            raise TypeError("reasons must contain DecisionReason values")


@dataclass(frozen=True, slots=True, kw_only=True)
class PlacementEvaluated(TraceEvent):
    bin_id: int
    feasible: bool
    remaining_before: int
    remaining_after: int | None
    score: float | None = None

    def __post_init__(self) -> None:
        super(PlacementEvaluated, self).__post_init__()
        if self.bin_id < 0 or self.remaining_before < 0:
            raise ValueError("bin_id and remaining_before must be non-negative")
        if self.feasible:
            if self.remaining_after is None or self.remaining_after < 0:
                raise ValueError("feasible placement requires non-negative remaining_after")
        elif self.remaining_after is not None:
            raise ValueError("infeasible placement requires remaining_after=None")
        if self.score is not None and not isfinite(self.score):
            raise ValueError("placement score must be finite")


@dataclass(frozen=True, slots=True, kw_only=True)
class PlacementSelected(TraceEvent):
    bin_id: int | None
    create_new_bin: bool

    def __post_init__(self) -> None:
        super(PlacementSelected, self).__post_init__()
        if self.create_new_bin == (self.bin_id is not None):
            raise ValueError("placement must select exactly one existing or new bin")
        if self.bin_id is not None and self.bin_id < 0:
            raise ValueError("bin_id must be non-negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class BinCreated(TraceEvent):
    bin_id: int
    capacity: int

    def __post_init__(self) -> None:
        super(BinCreated, self).__post_init__()
        if self.bin_id < 0 or self.capacity <= 0:
            raise ValueError("bin_id must be non-negative and capacity positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class ItemPlaced(TraceEvent):
    item_id: str
    bin_id: int
    used_capacity: int
    remaining_capacity: int

    def __post_init__(self) -> None:
        super(ItemPlaced, self).__post_init__()
        _nonempty(self.item_id, "item_id")
        if self.bin_id < 0 or self.used_capacity < 0 or self.remaining_capacity < 0:
            raise ValueError("placement capacities and bin_id must be non-negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class RunFinished(TraceEvent):
    bins_used: int
    total_capacity: int
    used_capacity: int
    unused_capacity: int
    utilization: float
    lower_bound: int
    placement_evaluations: int = 0

    def __post_init__(self) -> None:
        super(RunFinished, self).__post_init__()
        if min(
            self.bins_used,
            self.total_capacity,
            self.used_capacity,
            self.unused_capacity,
            self.lower_bound,
            self.placement_evaluations,
        ) < 0:
            raise ValueError("run summary counts must be non-negative")
        if self.used_capacity + self.unused_capacity != self.total_capacity:
            raise ValueError("used_capacity + unused_capacity must equal total_capacity")
        if not 0.0 <= self.utilization <= 1.0:
            raise ValueError("utilization must be in [0, 1]")
        if self.lower_bound > self.bins_used:
            raise ValueError("lower_bound cannot exceed bins_used")


TraceEventType = (
    RunStarted
    | ItemSelected
    | StateObserved
    | HeuristicSelected
    | PlacementEvaluated
    | PlacementSelected
    | BinCreated
    | ItemPlaced
    | RunFinished
)
