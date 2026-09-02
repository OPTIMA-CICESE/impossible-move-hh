from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping, Sequence

from impossible_move.domain.models import BinPackingStateView, Item
from impossible_move.explainability import DecisionReason


@dataclass(frozen=True, slots=True)
class PlacementDecision:
    bin_id: int | None = None
    create_new_bin: bool = False

    def __post_init__(self) -> None:
        if self.create_new_bin and self.bin_id is not None:
            raise ValueError("new-bin decisions cannot also reference an existing bin")
        if not self.create_new_bin and self.bin_id is None:
            raise ValueError("placement decision must select a bin or create a new one")
        if self.bin_id is not None and self.bin_id < 0:
            raise ValueError("bin_id must be non-negative")


@dataclass(frozen=True, slots=True)
class PlacementEvaluation:
    bin_id: int
    feasible: bool
    remaining_before: int
    remaining_after: int | None
    score: float | None = None

    def __post_init__(self) -> None:
        if self.bin_id < 0:
            raise ValueError("bin_id must be non-negative")
        if self.remaining_before < 0:
            raise ValueError("remaining_before must be non-negative")
        if self.feasible:
            if self.remaining_after is None or self.remaining_after < 0:
                raise ValueError("feasible evaluations require non-negative remaining_after")
            if self.remaining_after > self.remaining_before:
                raise ValueError("remaining_after cannot exceed remaining_before")
        elif self.remaining_after is not None:
            raise ValueError("infeasible evaluations must use remaining_after=None")
        if self.score is not None and not isfinite(self.score):
            raise ValueError("evaluation score must be finite")


@dataclass(frozen=True, slots=True)
class PlacementResult:
    decision: PlacementDecision
    evaluations: tuple[PlacementEvaluation, ...] = ()


@dataclass(frozen=True, slots=True)
class HeuristicSelection:
    heuristic_id: str
    scores: Mapping[str, float] | None = None
    reasons: tuple[DecisionReason, ...] = ()

    def __post_init__(self) -> None:
        if not self.heuristic_id.strip():
            raise ValueError("heuristic_id must be non-empty")
        if self.scores is not None:
            copied = dict(self.scores)
            if any(not key.strip() for key in copied):
                raise ValueError("score heuristic ids must be non-empty")
            if any(not isfinite(value) for value in copied.values()):
                raise ValueError("heuristic scores must be finite")
            object.__setattr__(self, "scores", MappingProxyType(copied))
        if any(not isinstance(reason, DecisionReason) for reason in self.reasons):
            raise TypeError("reasons must contain DecisionReason values")


class ItemOrderingStrategy(ABC):
    id: str

    @abstractmethod
    def order(self, items: Sequence[Item]) -> list[Item]:
        """Return a new list containing the processing order."""


class LowLevelHeuristic(ABC):
    id: str
    display_name: str

    def reset(self) -> None:
        """Reset per-run state. Stateless heuristics need no action."""

    @abstractmethod
    def choose_placement(self, item: Item, state: BinPackingStateView) -> PlacementResult:
        """Propose a placement without mutating state."""


class HyperHeuristic(ABC):
    id: str
    display_name: str

    def reset(self) -> None:
        """Reset per-run state before a new solve."""

    @abstractmethod
    def select(
        self,
        state: BinPackingStateView,
        available_heuristics: Sequence[LowLevelHeuristic],
    ) -> HeuristicSelection:
        """Select a low-level heuristic without mutating state."""
