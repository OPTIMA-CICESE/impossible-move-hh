from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from impossible_move.domain.models import BinPackingStateView
from impossible_move.explainability import DecisionReason
from impossible_move.optimization.contracts import (
    HeuristicSelection,
    HyperHeuristic,
    LowLevelHeuristic,
)
from impossible_move.optimization.features import extract_bin_packing_features


@dataclass(frozen=True, slots=True)
class RuleBasedHHConfig:
    small_item_ratio: float = 0.30
    large_item_ratio: float = 0.60
    high_residual_spread: float = 0.40
    tight_last_bin_ratio: float = 0.20

    base_first_fit: float = 1.00
    base_best_fit: float = 1.00
    base_worst_fit: float = 0.35
    base_next_fit: float = 0.20

    no_existing_fit_first_fit: float = 4.00
    exact_fit_best_fit: float = 4.00
    single_feasible_first_fit: float = 1.50
    single_feasible_best_fit: float = 0.50
    large_item_best_fit: float = 2.00
    small_item_worst_fit: float = 1.25
    medium_item_first_fit: float = 0.75
    high_spread_best_fit: float = 1.00
    tight_last_bin_next_fit: float = 2.50

    def __post_init__(self) -> None:
        ratios = (
            self.small_item_ratio,
            self.large_item_ratio,
            self.high_residual_spread,
            self.tight_last_bin_ratio,
        )
        if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in ratios):
            raise ValueError("all rule thresholds must be finite values in [0, 1]")
        if self.small_item_ratio >= self.large_item_ratio:
            raise ValueError("small_item_ratio must be strictly below large_item_ratio")

        weights = (
            self.base_first_fit,
            self.base_best_fit,
            self.base_worst_fit,
            self.base_next_fit,
            self.no_existing_fit_first_fit,
            self.exact_fit_best_fit,
            self.single_feasible_first_fit,
            self.single_feasible_best_fit,
            self.large_item_best_fit,
            self.small_item_worst_fit,
            self.medium_item_first_fit,
            self.high_spread_best_fit,
            self.tight_last_bin_next_fit,
        )
        if any(not isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("all rule weights must be finite and non-negative")


class ExplainableRuleBasedHH(HyperHeuristic):
    """Deterministic, state-based selective hyper-heuristic for outreach.

    The HH accumulates transparent score contributions for First Fit, Best Fit,
    Worst Fit and Next Fit. Every contribution is emitted as a DecisionReason,
    so the final score can be reconstructed exactly from the trace.
    """

    id = "explainable_rule_based"
    display_name = "Explainable Rule-Based Hyper-Heuristic"

    SUPPORTED_IDS = ("first_fit", "best_fit", "worst_fit", "next_fit")
    TIE_BREAK_ORDER = ("best_fit", "first_fit", "worst_fit", "next_fit")

    def __init__(self, config: RuleBasedHHConfig | None = None) -> None:
        self.config = config or RuleBasedHHConfig()

    def select(
        self,
        state: BinPackingStateView,
        available_heuristics: Sequence[LowLevelHeuristic],
    ) -> HeuristicSelection:
        if state.current_item is None:
            raise RuntimeError("ExplainableRuleBasedHH requires an active current_item")
        if not available_heuristics:
            raise ValueError("ExplainableRuleBasedHH requires at least one heuristic")

        ids = [heuristic.id for heuristic in available_heuristics]
        if len(ids) != len(set(ids)):
            raise ValueError("available heuristic ids must be unique")
        unsupported = sorted(set(ids) - set(self.SUPPORTED_IDS))
        if unsupported:
            raise ValueError(
                "ExplainableRuleBasedHH only supports First/Best/Worst/Next Fit; "
                f"unsupported ids={unsupported!r}"
            )

        available = set(ids)
        scores = {heuristic_id: 0.0 for heuristic_id in ids}
        reasons: list[DecisionReason] = []

        def contribute(rule_id: str, heuristic_id: str, amount: float) -> None:
            if heuristic_id not in available or amount == 0.0:
                return
            scores[heuristic_id] += amount
            reasons.append(
                DecisionReason(
                    rule_id=rule_id,
                    heuristic_id=heuristic_id,
                    contribution=amount,
                )
            )

        cfg = self.config
        for heuristic_id, base in (
            ("first_fit", cfg.base_first_fit),
            ("best_fit", cfg.base_best_fit),
            ("worst_fit", cfg.base_worst_fit),
            ("next_fit", cfg.base_next_fit),
        ):
            contribute("base", heuristic_id, base)

        features = extract_bin_packing_features(state)
        feasible_bins = int(features["feasible_bins"])
        exact_fit_bins = int(features["exact_fit_bins"])
        item_ratio = features["item_ratio"]
        residual_spread = features["residual_spread"]
        last_bin_feasible = bool(features["last_bin_feasible"])
        last_bin_remaining_after = features["last_bin_remaining_after"]
        capacity = state.instance.capacity

        if feasible_bins == 0:
            contribute("no_existing_fit", "first_fit", cfg.no_existing_fit_first_fit)

        if exact_fit_bins > 0:
            contribute("exact_fit", "best_fit", cfg.exact_fit_best_fit)

        if feasible_bins == 1:
            contribute("single_feasible_bin", "first_fit", cfg.single_feasible_first_fit)
            contribute("single_feasible_bin", "best_fit", cfg.single_feasible_best_fit)

        if item_ratio >= cfg.large_item_ratio:
            contribute("large_item", "best_fit", cfg.large_item_best_fit)
        elif item_ratio <= cfg.small_item_ratio:
            if feasible_bins >= 2:
                contribute("small_item_many_options", "worst_fit", cfg.small_item_worst_fit)
        else:
            contribute("medium_item", "first_fit", cfg.medium_item_first_fit)

        if residual_spread >= cfg.high_residual_spread:
            contribute("high_residual_spread", "best_fit", cfg.high_spread_best_fit)

        if last_bin_feasible:
            last_after_ratio = last_bin_remaining_after / capacity
            if last_after_ratio <= cfg.tight_last_bin_ratio:
                contribute("tight_last_bin", "next_fit", cfg.tight_last_bin_next_fit)

        max_score = max(scores.values())
        tied = {heuristic_id for heuristic_id, score in scores.items() if score == max_score}
        selected_id = next(
            heuristic_id
            for heuristic_id in self.TIE_BREAK_ORDER
            if heuristic_id in tied
        )

        return HeuristicSelection(
            heuristic_id=selected_id,
            scores=scores,
            reasons=tuple(reasons),
        )
