from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from impossible_move.domain.models import BinPackingInstance
from impossible_move.replay import ReplayCatalog
from impossible_move.trace.trace import RunTrace


POLICY_ADAPTIVE = "adaptive"
POLICY_RANDOM = "random"
POLICY_FIXED = "fixed"
SUPPORTED_POLICIES = (POLICY_ADAPTIVE, POLICY_RANDOM, POLICY_FIXED)


@dataclass(frozen=True, slots=True)
class ResolvedPolicyRun:
    policy_id: str
    label: str
    trace: RunTrace
    catalog: ReplayCatalog
    bins_used: int
    lower_bound: int
    utilization: float
    fixed_heuristic_id: str | None = None

    @property
    def gap(self) -> int:
        return self.bins_used - self.lower_bound


@dataclass(frozen=True, slots=True)
class ResolvedComparison:
    instance: BinPackingInstance
    instance_seed: int
    runs: Mapping[str, ResolvedPolicyRun]
    selected_policies: tuple[str, ...]
    fixed_heuristic_id: str
    fixed_benchmarks: Mapping[str, int]
    best_fixed_heuristic_id: str | None
    best_fixed_bins: int | None

    @property
    def adaptive_delta_to_best_fixed(self) -> int | None:
        adaptive = self.runs.get(POLICY_ADAPTIVE)
        if adaptive is None or self.best_fixed_bins is None:
            return None
        return adaptive.bins_used - self.best_fixed_bins

    @property
    def adaptive_classification(self) -> str:
        delta = self.adaptive_delta_to_best_fixed
        if delta is None:
            return "not_available"
        if delta < 0:
            return "adaptive_opportunity"
        if delta > 0:
            return "fixed_friendly"
        return "tie"
